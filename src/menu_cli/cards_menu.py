import copy
import logging

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.mapping import (ignored_tables, map_field_ids_by_table_id,
                               replace_table_names_in_query, table_mapping)
from src.utils.print_cards import print_card_details
from src.utils.screen_contact import clear_screen

logger = logging.getLogger(__name__)

# --- Global cache ---
TABLE_ID_CACHE = {}


def list_cards(manager: MetabaseAPIManager):
    cards = manager.card.list_all_cards()
    clear_screen()
    print('📄 All Cards')
    print('=' * 60)
    for c in cards:
        print(f"[{c['id']}] {c['name']}")


def view_card(manager: MetabaseAPIManager, cid: int):
    card = manager.card.get_card_detail(cid)
    clear_screen()
    print_card_details(card)
    input('🔙 Press Enter to return...')


def create_card(manager: MetabaseAPIManager):
    print('🔧 Create card → Function in development')
    input('🔙 Press Enter to return...')


# ---------------- Field & Table Mapping ----------------


def find_new_table_id(old_table_id: int, old_tables: list[dict],
                      new_tables: list[dict], table_mapping: dict) -> int:
    global TABLE_ID_CACHE
    if old_table_id in TABLE_ID_CACHE:
        return TABLE_ID_CACHE[old_table_id]

    old_table = next(
        (t for t in old_tables if t.get('table_id') == old_table_id), None)
    if not old_table:
        logger.warning('Không tìm thấy old_table_id %s trong old_tables',
                       old_table_id)
        TABLE_ID_CACHE[old_table_id] = None
        return None

    old_table_name = old_table.get('table_name', '')
    old_table_name_short = old_table_name.split('.')[-1]

    # Tìm mapping từ table_mapping
    mapped_full = next((new_full
                        for full_old, new_full in table_mapping.items()
                        if full_old.endswith(old_table_name_short)), None)
    if mapped_full:
        mapped_table_name_short = mapped_full.split('.')[-1]
    else:
        # Nếu không có mapping, dùng luôn tên cũ
        mapped_table_name_short = old_table_name_short

    new_table = next(
        (t for t in new_tables
         if t.get('table_name', '').split('.')[-1] == mapped_table_name_short),
        None)

    TABLE_ID_CACHE[old_table_id] = new_table.get(
        'table_id') if new_table else None
    if not new_table:
        logger.warning('Không tìm thấy new_table cho old_table %s (%s)',
                       old_table_name, old_table_id)
    return TABLE_ID_CACHE[old_table_id]


def remap_field_ids(obj, field_mapping: dict):
    if isinstance(obj, list):
        if len(obj) >= 2 and obj[0] == 'field' and isinstance(obj[1], int):
            old_id = obj[1]
            new_id = field_mapping.get(old_id, old_id)
            return ['field', new_id] + [
                remap_field_ids(item, field_mapping) for item in obj[2:]
            ]
        return [remap_field_ids(item, field_mapping) for item in obj]
    if isinstance(obj, dict):
        return {k: remap_field_ids(v, field_mapping) for k, v in obj.items()}
    return obj


def build_global_field_mapping(old_db_id: int, new_db_id: int,
                               manager: MetabaseAPIManager) -> dict:
    try:
        old_tables = manager.database.get_all_table_in_specific_db(old_db_id)
    except Exception:
        logger.exception('Failed to fetch tables for old_db %s', old_db_id)
        old_tables = []

    try:
        new_tables = manager.database.get_all_table_in_specific_db(new_db_id)
    except Exception:
        logger.exception('Failed to fetch tables for new_db %s', new_db_id)
        new_tables = []

    try:
        old_fields = manager.database.get_fields_in_specific_db(old_db_id)
    except Exception:
        logger.exception('Failed to fetch fields for old_db %s', old_db_id)
        old_fields = []

    try:
        new_fields = manager.database.get_fields_in_specific_db(new_db_id)
    except Exception:
        logger.exception('Failed to fetch fields for new_db %s', new_db_id)
        new_fields = []

    global_mapping = {}
    for old_table in old_tables:
        new_table_id = find_new_table_id(old_table['table_id'], old_tables,
                                         new_tables, table_mapping)
        if new_table_id:
            mapping = map_field_ids_by_table_id(
                old_fields=old_fields,
                new_fields=new_fields,
                old_table_id=old_table['table_id'],
                new_table_id=new_table_id)
            global_mapping.update(mapping)

    logger.info('✅ Global field mapping built: %d fields', len(global_mapping))
    return global_mapping


# ---------------- Process Card ----------------


def process_card(card_detail: dict,
                 global_field_mapping: dict,
                 new_db_id: int,
                 table_mapping: dict,
                 old_tables: list[dict] = None,
                 new_tables: list[dict] = None) -> dict:
    updated_card = copy.deepcopy(card_detail)
    dataset_query = updated_card.get('dataset_query', {})

    # Always update database
    updated_card['database_id'] = new_db_id
    dataset_query['database'] = new_db_id

    query_type = updated_card.get('query_type')
    if query_type == 'query':
        query = dataset_query.get('query', {})
        old_table_id = query.get('source-table')
        if old_table_id and old_tables and new_tables:
            new_table_id = find_new_table_id(old_table_id, old_tables,
                                             new_tables, table_mapping)
            if new_table_id:
                query['source-table'] = new_table_id
        for key in [
                'breakout', 'aggregation', 'filter', 'expressions', 'order-by'
        ]:
            if key in query:
                query[key] = remap_field_ids(query[key], global_field_mapping)
        dataset_query['query'] = query

    elif query_type == 'native':
        native = dataset_query.get('native', {})
        sql_query = native.get('query')
        if sql_query:
            native['query'] = replace_table_names_in_query(
                sql_query, table_mapping)
        tags = native.get('template-tags', {})
        for tag_info in tags.values():
            dimension = tag_info.get('dimension')
            if isinstance(
                    dimension,
                    list) and len(dimension) >= 2 and dimension[0] == 'field':
                tag_info['dimension'][1] = global_field_mapping.get(
                    dimension[1], dimension[1])
        dataset_query['native'] = native

    updated_card['dataset_query'] = dataset_query
    return updated_card


# ---------------- Update / Delete Cards ----------------


def update_cards(manager: MetabaseAPIManager):
    print('=== 🔧 Update Cards Database/Table ===')
    print('1️⃣  Update ALL cards')
    print('2️⃣  Update cards in a specific collection')
    print('3️⃣  Update cards in a specific dashboard')
    print('4️⃣  Update specific card IDs (comma separated)')
    print('0️⃣  Cancel')

    choice = input_int('👉 Choose an option (0-4): ')
    if choice == 0:
        print('❌ Cancelled.')
        return

    all_cards = manager.card.list_all_cards()
    card_ids = []

    if choice == 1:
        card_ids = [c['id'] for c in all_cards]
    elif choice == 2:
        collection_id = input_int('Enter collection ID: ')
        card_ids = [
            c['id'] for c in all_cards
            if c.get('collection_id') == collection_id
        ]
    elif choice == 3:
        dashboard_id = input_int('Enter dashboard ID: ')
        card_ids = [
            c['id'] for c in all_cards if c.get('dashboard_id') == dashboard_id
        ]
    elif choice == 4:
        ids_str = input_str('Enter card IDs separated by comma: ')
        card_ids = [
            int(cid.strip()) for cid in ids_str.split(',')
            if cid.strip().isdigit()
        ]
    else:
        print('❌ Invalid choice.')
        return

    if not card_ids:
        print('⚠️ No cards found. Exiting.')
        return

    print(f'✅ Found {len(card_ids)} card(s) to update.')

    first_card_db = next(
        (manager.card.get_card_detail(cid).get('database_id')
         for cid in card_ids
         if manager.card.get_card_detail(cid).get('database_id') is not None),
        None)

    database_id_new = input_int(
        'Enter new database ID (leave blank to keep current): ',
        allow_empty=True)
    if database_id_new is None:
        database_id_new = first_card_db

    if database_id_new is None:
        print('❌ Không xác định được database mới. Exiting.')
        return

    global_field_mapping = build_global_field_mapping(first_card_db,
                                                      database_id_new, manager)
    dry_run = not input_yes_no(
        'Do you want to APPLY changes? (Answer NO to perform a dry-run)')
    if dry_run:
        print(
            '--- Running in dry-run mode; no updates will be sent to the API ---'
        )

    tables_cache = {}
    for cid in card_ids:
        try:
            card_detail = manager.card.get_card_detail(cid)
            old_db_id = card_detail.get('database_id')

            for db_id in [old_db_id, database_id_new]:
                if db_id not in tables_cache:
                    try:
                        tables_cache[
                            db_id] = manager.database.get_all_table_in_specific_db(
                                db_id)
                    except Exception:
                        tables_cache[db_id] = []

            updated_card = process_card(
                card_detail=card_detail,
                global_field_mapping=global_field_mapping,
                new_db_id=database_id_new,
                table_mapping=table_mapping,
                old_tables=tables_cache.get(old_db_id, []),
                new_tables=tables_cache.get(database_id_new, []))

            print(f'📝 Card ID: {cid} ({updated_card.get("name")})')

            if not dry_run:
                manager.card.update_specific_card(cid, updated_card)
                print('✅ Updated successfully.')
            else:
                print('💡 Dry-run only, not applied.')

        except Exception:
            logger.exception('Failed processing card %s', cid)

    print('🎯 Done updating cards.')
    input('🔙 Press Enter to return...')


def delete_card(manager: MetabaseAPIManager):
    cid = input_int("Enter card ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(f'Are you sure you want to delete card ID {cid}?')
    if confirm:
        res = manager.card.delete_specific_card(cid)
        if res.status_code < 400:
            print(f'Card ID {cid} deleted successfully.')
        else:
            print(
                f'Failed to delete card ID {cid}. Status code: {res.status_code}'
            )
    else:
        print('Delete cancelled.')

    input('🔙 Press Enter to return...')


def card_menu(manager: MetabaseAPIManager):
    while True:
        list_cards(manager)

        print('\nOptions:')
        print('  [id] - View card by ID')
        print('  c    - Create new card')
        print('  u    - Update card')
        print('  d    - Delete card')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'c':
            create_card(manager)
        elif action.lower() == 'u':
            update_cards(manager)
        elif action.lower() == 'd':
            delete_card(manager)
        elif action.isdigit():
            view_card(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
