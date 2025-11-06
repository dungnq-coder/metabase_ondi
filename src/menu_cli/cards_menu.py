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


# --- Global cache ---
TABLE_ID_CACHE = {}


def find_new_table_id(old_table_id: int, old_tables: list[dict],
                      new_tables: list[dict], table_mapping: dict) -> int:
    """Find new table_id for an old_table_id using the provided mapping.

    Returns new table_id or None if not found. Results are cached in
    TABLE_ID_CACHE to avoid repeated lookups.
    """
    global TABLE_ID_CACHE

    if old_table_id in TABLE_ID_CACHE:
        return TABLE_ID_CACHE[old_table_id]

    old_table = next(
        (t for t in old_tables if t.get('table_id') == old_table_id), None)
    if not old_table:
        logger.warning('Không tìm thấy old_table_id %s trong old_tables',
                       old_table_id)
        for t in old_tables:
            logger.debug(' old_table: table_id=%s, table_name=%s',
                         t.get('table_id'), t.get('table_name'))
        TABLE_ID_CACHE[old_table_id] = None
        return None

    old_table_name = str(old_table.get('table_name', '')).split('.')[-1]

    # Try to find mapping that endswith the old tail name; fall back to same full name
    mapped_full = None
    for full_old, full_new in table_mapping.items():
        if str(full_old).endswith(old_table_name):
            mapped_full = full_new
            break

    if not mapped_full:
        mapped_full = old_table.get('table_name')

    mapped_table_name = str(mapped_full).split('.')[-1]
    logger.debug('Card trỏ tới old_table_id=%s (%s) -> mapped_table_name=%s',
                 old_table_id, old_table_name, mapped_table_name)

    for t in new_tables:
        new_table_name = str(t.get('table_name', '')).split('.')[-1]
        logger.debug(' Checking new_table: table_id=%s, table_name=%s',
                     t.get('table_id'), new_table_name)
        if new_table_name == mapped_table_name:
            logger.info('Tìm thấy table mới: table_id=%s, table_name=%s',
                        t.get('table_id'), new_table_name)
            TABLE_ID_CACHE[old_table_id] = t.get('table_id')
            return t.get('table_id')

    logger.warning("Không tìm thấy bảng mới tương ứng cho '%s' → '%s'",
                   old_table_name, mapped_table_name)
    TABLE_ID_CACHE[old_table_id] = None
    return None


def remap_field_ids(obj, field_mapping: dict):
    """Recursively remap field ids in a nested structure used in Metabase queries.

    Supports lists and dicts. Leaves other types unchanged.
    """
    if isinstance(obj, list):
        if len(obj) >= 2 and obj[0] == 'field' and isinstance(obj[1], int):
            old_id = obj[1]
            new_id = field_mapping.get(old_id, old_id)
            new_obj = ['field', new_id]
            for i in range(2, len(obj)):
                new_obj.append(remap_field_ids(obj[i], field_mapping))
            return new_obj
        else:
            return [remap_field_ids(item, field_mapping) for item in obj]

    if isinstance(obj, dict):
        return {k: remap_field_ids(v, field_mapping) for k, v in obj.items()}

    return obj


def process_native_card(card_detail: dict, field_mapping: dict,
                        new_db_id: int) -> dict:
    updated = copy.deepcopy(card_detail)
    dataset_query = updated.get('dataset_query', {})

    # Update database
    dataset_query['database'] = new_db_id
    updated['database_id'] = new_db_id

    # Update field_id trong template-tags
    native_part = dataset_query.get('native', {})
    tags = native_part.get('template-tags', {})

    for tag_name, tag_info in tags.items():
        dimension = tag_info.get('dimension')
        if isinstance(
                dimension,
                list) and len(dimension) >= 2 and dimension[0] == 'field':
            old_id = dimension[1]
            if old_id in field_mapping:
                tag_info['dimension'][1] = field_mapping[old_id]
                logger.info("Updated field ID for tag '%s': %s → %s", tag_name,
                            old_id, tag_info['dimension'][1])

    updated['dataset_query'] = dataset_query
    return updated


def process_query_card(card_detail: dict, field_mapping: dict, new_db_id: int,
                       new_table_id: int) -> dict:
    updated = copy.deepcopy(card_detail)
    dataset_query = updated.get('dataset_query', {})
    query = dataset_query.get('query', {})

    # Update database/table
    dataset_query['database'] = new_db_id
    updated['database_id'] = new_db_id
    if 'source-table' in query and new_table_id is not None:
        query['source-table'] = new_table_id

    # Remap field_ids
    for key in ['breakout', 'aggregation', 'filter']:
        if key in query:
            query[key] = remap_field_ids(query[key], field_mapping)

    if 'expressions' in query:
        query['expressions'] = remap_field_ids(query['expressions'],
                                               field_mapping)

    if 'order-by' in query:
        query['order-by'] = remap_field_ids(query['order-by'], field_mapping)

    updated['dataset_query']['query'] = query
    return updated


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

    # --- Lấy database cũ từ card đầu tiên nếu user không nhập ---
    first_card_db = None
    for cid in card_ids:
        try:
            first_card_db = manager.card.get_card_detail(cid).get(
                'database_id')
            if first_card_db is not None:
                break
        except Exception:
            logger.exception(
                'Failed to fetch card detail for %s when looking up first DB',
                cid)

    database_id_new = input_int(
        'Enter new database ID (leave blank to keep current): ',
        allow_empty=True)

    # input_int with allow_empty returns None when user leaves blank
    if database_id_new is None:
        database_id_new = first_card_db

    if database_id_new is None:
        print('❌ Không xác định được database mới. Exiting.')
        return

    # Ask dry-run
    dry_run = not input_yes_no(
        'Do you want to APPLY changes? (Answer NO to perform a dry-run)')
    if dry_run:
        print(
            '--- Running in dry-run mode; no updates will be sent to the API ---'
        )

    # --- Update từng card (with per-DB cache and per-card error handling) ---
    tables_cache = {}
    fields_cache = {}

    for cid in card_ids:
        try:
            card_detail = manager.card.get_card_detail(cid)
        except Exception as exc:
            logger.exception('Failed to fetch card detail for %s: %s', cid,
                             exc)
            continue

        query_type = card_detail.get('query_type')
        updated_card = None

        try:
            if query_type == 'query':
                old_db_id = card_detail.get('database_id')
                old_table_id = card_detail.get('dataset_query',
                                               {}).get('query',
                                                       {}).get('source-table')

                if old_db_id not in tables_cache:
                    try:
                        tables_cache[
                            old_db_id] = manager.database.get_all_table_in_specific_db(
                                old_db_id)
                    except Exception:
                        logger.exception(
                            'Failed to fetch tables for old_db %s', old_db_id)
                        tables_cache[old_db_id] = []

                if database_id_new not in tables_cache:
                    try:
                        tables_cache[
                            database_id_new] = manager.database.get_all_table_in_specific_db(
                                database_id_new)
                    except Exception:
                        logger.exception(
                            'Failed to fetch tables for new_db %s',
                            database_id_new)
                        tables_cache[database_id_new] = []

                if old_db_id not in fields_cache:
                    try:
                        fields_cache[
                            old_db_id] = manager.database.get_fields_in_specific_db(
                                old_db_id)
                    except Exception:
                        logger.exception(
                            'Failed to fetch fields for old_db %s', old_db_id)
                        fields_cache[old_db_id] = []

                if database_id_new not in fields_cache:
                    try:
                        fields_cache[
                            database_id_new] = manager.database.get_fields_in_specific_db(
                                database_id_new)
                    except Exception:
                        logger.exception(
                            'Failed to fetch fields for new_db %s',
                            database_id_new)
                        fields_cache[database_id_new] = []

                old_tables = tables_cache.get(old_db_id, [])
                new_tables = tables_cache.get(database_id_new, [])
                old_fields = fields_cache.get(old_db_id, [])
                new_fields = fields_cache.get(database_id_new, [])

                new_table_id = find_new_table_id(old_table_id, old_tables,
                                                 new_tables, table_mapping)
                if new_table_id is None:
                    logger.warning(
                        'Skipping card %s because new_table_id not found for old_table_id %s',
                        cid, old_table_id)
                    continue

                field_mapping = map_field_ids_by_table_id(
                    old_fields=old_fields,
                    new_fields=new_fields,
                    old_table_id=old_table_id,
                    new_table_id=new_table_id)

                updated_card = process_query_card(card_detail, field_mapping,
                                                  database_id_new,
                                                  new_table_id)

            elif query_type == 'native':
                native_query = card_detail.get('dataset_query',
                                               {}).get('native',
                                                       {}).get('query')
                if native_query:
                    updated_query = replace_table_names_in_query(
                        native_query, table_mapping)
                    logger.info(
                        'Card %s native query updated. Old: %s New: %s', cid,
                        native_query, updated_query)
                    updated = copy.deepcopy(card_detail)
                    updated['dataset_query']['native']['query'] = updated_query
                    updated['database_id'] = database_id_new
                    updated_card = updated
                else:
                    logger.warning(
                        'Card %s is native but has no query to update', cid)
                    continue

            else:
                logger.warning('Card %s has unknown query_type: %s', cid,
                               query_type)
                continue

            # Apply or display
            if dry_run:
                print(
                    f'[DRY-RUN] Card {cid} would be updated. New database_id={database_id_new}'
                )
                continue

            response = manager.card.update_specific_card(cid, updated_card)
            if hasattr(response, 'status_code'):
                success = response.status_code < 400
            elif isinstance(response, dict):
                success = 'id' in response
            else:
                success = False

            if success:
                print(f'✅ Card ID {cid} updated successfully.')
            else:
                print(f'❌ Failed to update Card ID {cid}: {response}')

        except Exception as exc:
            logger.exception('Error while processing/updating card %s: %s',
                             cid, exc)
            continue

    input('\n🔙 Press Enter to return to menu...')


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
