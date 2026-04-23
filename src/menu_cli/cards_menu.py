import copy
import logging

import requests

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.mapping import (ignored_tables, map_field_ids_by_table_id,
                               replace_table_names_in_query, table_mapping_bl,
                               table_mapping_nw, table_mapping_sr)
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
        TABLE_ID_CACHE[old_table_id] = None
        return None

    old_table_name = old_table.get('table_name', '')
    old_table_name_short = old_table_name.split('.')[-1]

    # Tìm mapping theo full name trước, fallback sang short name
    mapped_full = table_mapping.get(old_table_name)
    if not mapped_full:
        mapped_full = next((new_full
                            for full_old, new_full in table_mapping.items()
                            if full_old.split('.')[-1] == old_table_name_short),
                           None)
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
    return TABLE_ID_CACHE[old_table_id]


def remap_field_ids(obj, field_mapping: dict):
    if isinstance(obj, list):
        # Handle Metabase field refs that can be either:
        # ['field', <id>, ...] or ['field', {meta}, <id>, ...]
        if len(obj) >= 2 and obj[0] == 'field':
            # find first integer index after position 0
            field_idx = None
            for idx in range(1, len(obj)):
                if isinstance(obj[idx], int):
                    field_idx = idx
                    break
            if field_idx is not None:
                old_id = obj[field_idx]
                new_id = field_mapping.get(old_id, old_id)
                new_list = []
                for i, item in enumerate(obj):
                    if i == field_idx:
                        new_list.append(new_id)
                    elif i == 0:
                        new_list.append('field')
                    else:
                        new_list.append(remap_field_ids(item, field_mapping))
                return new_list
        return [remap_field_ids(item, field_mapping) for item in obj]
    if isinstance(obj, dict):
        return {k: remap_field_ids(v, field_mapping) for k, v in obj.items()}
    return obj


def remap_template_tags_in(obj, field_mapping: dict):
    """Recursively find `template-tags` dicts and remap any ['field', id, ...] dimensions."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'template-tags' and isinstance(v, dict):
                for tag_name, tag_info in v.items():
                    if isinstance(tag_info, dict) and 'dimension' in tag_info:
                        tag_info['dimension'] = remap_field_ids(
                            tag_info['dimension'], field_mapping)
            else:
                remap_template_tags_in(v, field_mapping)
    elif isinstance(obj, list):
        for item in obj:
            remap_template_tags_in(item, field_mapping)
    return obj


def remove_unmapped_template_tags(obj, field_mapping: dict):
    """Keep template-tags and remap their field ids when possible.
    Unmapped field ids are preserved (no tag deletion)."""
    if not isinstance(obj, dict):
        return obj

    if 'template-tags' in obj and isinstance(obj['template-tags'], dict):
        tags = obj['template-tags']
        for tag_name, tag_info in tags.items():
            if isinstance(tag_info, dict) and 'dimension' in tag_info:
                dim = tag_info['dimension']
                # find first integer in dim
                field_idx = None
                if isinstance(dim, list):
                    for idx in range(1, len(dim)):
                        if isinstance(dim[idx], int):
                            field_idx = idx
                            break
                if field_idx is not None:
                    old_id = dim[field_idx]
                    new_id = field_mapping.get(old_id)
                    if new_id and new_id != old_id:
                        dim[field_idx] = new_id
                    else:
                        logger.warning(
                            "Template tag '%s' keeps unmapped field id %s",
                            tag_name, old_id)

    # recurse into nested structures
    for k, v in list(obj.items()):
        if isinstance(v, dict):
            remove_unmapped_template_tags(v, field_mapping)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    remove_unmapped_template_tags(item, field_mapping)

    return obj


def remap_template_tags_with_table_fallback(dataset_query: dict,
                                            field_mapping: dict,
                                            old_fields: list[dict],
                                            new_fields: list[dict],
                                            old_tables: list[dict],
                                            new_tables: list[dict],
                                            table_mapping: dict):
    """Remap template-tag field ids with fallback by old-field metadata.

    Priority:
    1) direct old_id -> new_id from field_mapping
    2) old field metadata (name + table_id) -> mapped new table_id -> new field id
    3) fallback by field name globally in target DB
    """
    if not isinstance(dataset_query, dict):
        return []

    old_field_by_id = {f.get('id'): f for f in old_fields if isinstance(f, dict)}
    new_field_by_table_and_name = {
        (f.get('table_id'), (f.get('name') or '').lower()): f.get('id')
        for f in new_fields if isinstance(f, dict)
    }
    new_field_by_name = {
        (f.get('name') or '').lower(): f.get('id')
        for f in new_fields if isinstance(f, dict)
    }

    unresolved = []

    def _walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'template-tags' and isinstance(v, dict):
                    for tag_name, tag_info in v.items():
                        if not isinstance(tag_info, dict):
                            continue
                        dim = tag_info.get('dimension')
                        if not (isinstance(dim, list) and len(dim) >= 2
                                and dim[0] == 'field'):
                            continue

                        field_idx = None
                        for idx in range(1, len(dim)):
                            if isinstance(dim[idx], int):
                                field_idx = idx
                                break
                        if field_idx is None:
                            continue

                        old_id = dim[field_idx]
                        new_id = field_mapping.get(old_id)

                        if not new_id:
                            old_field = old_field_by_id.get(old_id)
                            if old_field:
                                old_name = (old_field.get('name') or '').lower()
                                old_table_id = old_field.get('table_id')
                                new_table_id = find_new_table_id(
                                    old_table_id, old_tables, new_tables,
                                    table_mapping) if old_table_id else None
                                if new_table_id and old_name:
                                    new_id = new_field_by_table_and_name.get(
                                        (new_table_id, old_name))
                                if not new_id and old_name:
                                    new_id = new_field_by_name.get(old_name)

                        if not new_id:
                            tag_key_name = (tag_info.get('name')
                                            or tag_name or '').lower()
                            if tag_key_name:
                                new_id = new_field_by_name.get(tag_key_name)

                        if new_id:
                            dim[field_idx] = new_id
                            field_mapping[old_id] = new_id
                        else:
                            unresolved.append((tag_name, old_id))
                else:
                    _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(dataset_query)
    return unresolved


def build_global_field_mapping(old_db_id: int, new_db_id: int,
                               manager: MetabaseAPIManager,
                               table_mapping: dict) -> dict:
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


def special_process_card(manager: MetabaseAPIManager,
                         card_detail: dict) -> dict:
    update_cards = copy.deepcopy(card_detail)
    source_card_id = card_detail.get('source_card_id')
    name = manager.card.get_card_detail(source_card_id).get('name')

    dashboard_id = card_detail.get('dashboard_id')

    all_card = manager.card.list_all_cards()
    for c in all_card:
        if c['name'] == name and c['dashboard_id'] == dashboard_id and c[
                'id'] != card_detail.get('id'):
            update_cards['source_card_id'] = c['id']
            update_cards['dataset_query']['query'][
                'source-table'] = f'card__{c["id"]}'
            break
    return update_cards


def process_card(manager: MetabaseAPIManager,
                 card_detail: dict,
                 global_field_mapping: dict,
                 new_db_id: int,
                 table_mapping: dict,
                 old_tables: list[dict] = None,
                 new_tables: list[dict] = None) -> dict:
    card_id = card_detail.get('id')
    card_name = card_detail.get('name')
    print(f'[PROCESS] Starting card {card_id}: {card_name}')

    updated_card = copy.deepcopy(card_detail)
    dataset_query = updated_card.get('dataset_query', {})
    # keep a copy of the original dataset_query so we can fully restore it
    original_dataset_query = copy.deepcopy(dataset_query)

    old_db_id = updated_card['database_id']
    print(f'[PROCESS] Database: {old_db_id} → {new_db_id}')

    # Always update database
    updated_card['database_id'] = new_db_id
    dataset_query['database'] = new_db_id

    query_type = updated_card.get('query_type')
    print(f'[PROCESS] Query type: {query_type}')

    if updated_card.get('source_card_id') and manager is not None:
        print(
            f'[PROCESS] Card has source_card_id: {updated_card.get("source_card_id")}'
        )
        try:
            updated_card = special_process_card(manager, updated_card)
            print(f'[PROCESS] Special-processed card')
        except Exception as e:
            print(
                f"⚠️ Failed to special-process card {updated_card.get('id')}: {e}"
            )
        return updated_card

    if query_type == 'query':
        print(f'[PROCESS] Processing QUERY type')
        print(f'[PROCESS] dataset_query keys: {list(dataset_query.keys())}')

        # Support both the compact MBQL (`dataset_query['query']`) and
        # the full staged MBQL which places pieces directly on
        # `dataset_query` (has 'stages', 'expressions', 'breakout', ...).
        query = dataset_query.get('query') or dataset_query
        is_full_mbql = 'query' not in dataset_query

        # Try to discover the old table id from several possible locations
        old_table_id = None
        if isinstance(query, dict):
            old_table_id = (query.get('source-table') or query.get(
                'source-query', {}).get('source-table'))
            if not old_table_id and isinstance(query.get('stages'), list):
                for st in query.get('stages', []):
                    if st.get('source-table'):
                        old_table_id = st.get('source-table')
                        break

        # Fallback to top-level card.table_id (some cards include it)
        if not old_table_id:
            old_table_id = updated_card.get('table_id')

        print(f'[PROCESS] Old table ID: {old_table_id}')

        if not (old_table_id and old_tables and new_tables):
            print(
                f'[PROCESS] Missing data: table_id={old_table_id}, old_tables={bool(old_tables)}, new_tables={bool(new_tables)}'
            )
            return updated_card

        new_table_id = find_new_table_id(old_table_id, old_tables, new_tables,
                                         table_mapping)
        print(f'[PROCESS] New table ID resolved: {new_table_id}')

        if not new_table_id:
            print(f'[PROCESS] Could not resolve new table ID')
            return updated_card

        # Update table_id references in staged MBQL or in query object
        if is_full_mbql:
            for idx, st in enumerate(query.get('stages', [])):
                if 'source-table' in st and st.get(
                        'source-table') == old_table_id:
                    st['source-table'] = new_table_id
                # remap any field refs inside the stage
                query['stages'][idx] = remap_field_ids(
                    st, global_field_mapping)
            # also remap top-level expressions/breakout if present
            for key in [
                    'breakout', 'aggregation', 'filter', 'expressions',
                    'order-by'
            ]:
                if key in query:
                    query[key] = remap_field_ids(query[key],
                                                 global_field_mapping)
            # update card-level table_id if present
            updated_card['table_id'] = new_table_id
        else:
            source_query = query.get('source-query')
            if source_query is not None:
                query['source-query']['source-table'] = new_table_id
            else:
                query['source-table'] = new_table_id
            for key in [
                    'breakout', 'aggregation', 'filter', 'expressions',
                    'order-by'
            ]:
                if key in query:
                    query[key] = remap_field_ids(query[key],
                                                 global_field_mapping)

        print(f'[PROCESS] Updated table ID and remapped field IDs')

        # Remap result_metadata field refs and table_id entries
        try:
            for md in updated_card.get('result_metadata', []) or []:
                if isinstance(md, dict):
                    if 'field_ref' in md and isinstance(md['field_ref'], list):
                        md['field_ref'] = remap_field_ids(
                            md['field_ref'], global_field_mapping)
                    if md.get('table_id') == old_table_id:
                        md['table_id'] = new_table_id
        except Exception:
            logger.exception('Failed to remap result_metadata for card %s',
                             card_id)

        # ensure dataset_query is updated when original used top-level pieces
        if 'query' in dataset_query:
            dataset_query['query'] = query
        else:
            # when we modified `query` in-place above (is_full_mbql), dataset_query already points to it
            dataset_query = query

    elif query_type == 'native':
        print(f'[PROCESS] Processing NATIVE (SQL) type')
        print(f'[PROCESS] dataset_query keys: {list(dataset_query.keys())}')

        # Support both top-level native and staged MBQL (stages)
        native = dataset_query.get('native')
        staged_native = None
        native_stage_idx = None
        sql_query = None

        if native:
            # top-level: support {'query': ...} or {'native': ...}
            sql_query = native.get('query') or native.get('native')
            native_location = ('top', None)
        else:
            stages = dataset_query.get('stages') or []
            for idx, st in enumerate(stages):
                if st.get('lib/type') == 'mbql.stage/native' or 'native' in st:
                    staged_native = st
                    native_stage_idx = idx
                    sql_query = st.get('native') or st.get('query')
                    native_location = ('stage', idx)
                    break

        print(
            f'[PROCESS] Original SQL: {sql_query[:100] if sql_query else "None"}...'
        )

        change_db = False
        if sql_query:
            new_sql, change_db = replace_table_names_in_query(
                sql_query, table_mapping)
            print(
                f'[PROCESS] SQL after mapping: {new_sql[:100] if new_sql else "None"}...'
            )
            print(f'[PROCESS] change_db flag: {change_db}')

            # write back to the correct location
            if native_location[0] == 'top':
                if 'query' in native:
                    native['query'] = new_sql
                else:
                    native['native'] = new_sql
                dataset_query['native'] = native
            else:
                dataset_query.setdefault(
                    'stages', [])[native_stage_idx]['native'] = new_sql
        else:
            print(f'[PROCESS] No SQL query found')

        # Always update to new DB (user explicitly selected it)
        # and remap template-tags for the new DB
        tags = None
        if native:
            tags = native.get('template-tags', {})
        elif staged_native:
            tags = staged_native.get('template-tags', {})

        for tag_info in (tags.values() if tags else []):
            dimension = tag_info.get('dimension')
            if isinstance(
                    dimension,
                    list) and len(dimension) >= 2 and dimension[0] == 'field':
                field_index = None
                for idx in range(1, len(dimension)):
                    if isinstance(dimension[idx], int):
                        field_index = idx
                        break
                if field_index is not None:
                    old_id = dimension[field_index]
                    new_id = global_field_mapping.get(old_id, old_id)
                    tag_info['dimension'][field_index] = new_id

        if change_db:
            print(f'[PROCESS] SQL changed - database_id={new_db_id}')
        else:
            print(
                f'[PROCESS] SQL not changed but updating database_id to {new_db_id}'
            )

    updated_card['dataset_query'] = dataset_query
    print(
        f'[PROCESS] Final: DB={updated_card["database_id"]}, changed={updated_card["database_id"] != old_db_id}'
    )
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

    db_detail = manager.database.get_database_detail(
        database_id=database_id_new)
    db_name = db_detail.json().get('name', '').strip()

    # Safely generate a lowercase abbreviation from the first letter of each word
    short_db_name = ''.join(word[0].lower() for word in db_name.split()
                            if word)

    table_mapping = globals().get(f'table_mapping_{short_db_name}')

    if table_mapping is None:
        print(f'❌ No table mapping found for database: {db_name}')
        print(
            f'Available mappings: table_mapping_nw, table_mapping_sr, table_mapping_bl'
        )
        input('🔙 Press Enter to return...')
        return

    # avoid stale table-id cache across different update runs
    global TABLE_ID_CACHE
    TABLE_ID_CACHE = {}

    # cache field mapping by source DB (cards in selection can come from multiple DBs)
    field_mapping_by_old_db = {}
    dry_run = not input_yes_no(
        'Do you want to APPLY changes? (Answer NO to perform a dry-run)')
    if dry_run:
        print(
            '--- Running in dry-run mode; no updates will be sent to the API ---'
        )

    tables_cache = {}
    fields_cache = {}
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
                if db_id not in fields_cache:
                    try:
                        fields_cache[
                            db_id] = manager.database.get_fields_in_specific_db(
                                db_id)
                    except Exception:
                        fields_cache[db_id] = []

            if old_db_id not in field_mapping_by_old_db:
                field_mapping_by_old_db[old_db_id] = build_global_field_mapping(
                    old_db_id, database_id_new, manager, table_mapping)

            updated_card = process_card(
                manager=manager,
                card_detail=card_detail,
                global_field_mapping=field_mapping_by_old_db.get(old_db_id, {}),
                new_db_id=database_id_new,
                table_mapping=table_mapping,
                old_tables=tables_cache.get(old_db_id, []),
                new_tables=tables_cache.get(database_id_new, []))

            print(f'📝 Card ID: {cid} ({updated_card.get("name")})')

            if not dry_run:
                # Sanitize payload: keep only keys allowed by Metabase update API
                # Always set new DB and remap template-tags (user explicitly selected new DB)
                try:
                    updated_card['database_id'] = database_id_new
                    updated_card.setdefault('dataset_query',
                                            {})['database'] = database_id_new
                    card_field_mapping = field_mapping_by_old_db.get(
                        old_db_id, {})
                    unresolved_tags = remap_template_tags_with_table_fallback(
                        dataset_query=updated_card.get('dataset_query', {}),
                        field_mapping=card_field_mapping,
                        old_fields=fields_cache.get(old_db_id, []),
                        new_fields=fields_cache.get(database_id_new, []),
                        old_tables=tables_cache.get(old_db_id, []),
                        new_tables=tables_cache.get(database_id_new, []),
                        table_mapping=table_mapping)
                    remap_template_tags_in(
                        updated_card.get('dataset_query', {}),
                        card_field_mapping)
                    # Remove any remaining template-tags that couldn't be mapped
                    remove_unmapped_template_tags(
                        updated_card.get('dataset_query', {}),
                        card_field_mapping)
                    if unresolved_tags:
                        logger.warning(
                            'Card %s still has %d unresolved template tags: %s',
                            cid, len(unresolved_tags), unresolved_tags)
                except Exception:
                    logger.exception(
                        'Failed to remap template-tags for card %s', cid)

                allowed_keys = {
                    'name', 'dataset_query', 'display', 'description',
                    'archived', 'cache_ttl', 'collection_id',
                    'collection_position', 'collection_preview',
                    'dashboard_id', 'dashboard_tab_id',
                    'visualization_settings', 'embedding_params',
                    'embedding_type'
                }
                safe_payload = {
                    k: v
                    for k, v in updated_card.items() if k in allowed_keys
                }
                try:
                    manager.card.update_specific_card(cid, safe_payload)
                    print('✅ Updated successfully.')
                except requests.exceptions.HTTPError as e:
                    resp = getattr(e, 'response', None)
                    print('❌ Update failed with HTTPError')
                    print('Status:',
                          resp.status_code if resp is not None else 'N/A')
                    print('Response body:',
                          resp.text if resp is not None else 'N/A')
                    print('Payload sent:', safe_payload)
                    raise
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
