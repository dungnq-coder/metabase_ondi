# src/utils/print_cards.py
import re
from .format_time import format_time
from .icons import icon_bool, icon_display
from .permissions import format_permissions


def extract_table_from_sql(query: str) -> str:
    """Tìm tên bảng từ truy vấn SQL (đơn giản)."""
    if not query:
        return None

    # Regex tìm cụm sau FROM hoặc JOIN
    match = re.search(r'\bFROM\s+[`"]?([\w\.\-]+)[`"]?', query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def print_card_details(data: dict):
    if not data:
        print('❗ Data empty.')
        return

    print('\n📄 Card Details:')
    print('=' * 60)

    # ---- Basic Info ----
    print(f"🆔 ID             : {data.get('id')}")
    print(f"📛 Name           : {data.get('name')}")
    print(f"🗄️ Database ID    : {data.get('database_id')}")
    print(f"🗂️ Collection ID  : {data.get('collection_id')}")

    # ---- Table Info ----
    dataset_query = data.get('dataset_query') or {}
    table_id = None
    table_name = None

    # Metabase structured query
    if dataset_query.get('query', {}).get('source-table'):
        table_id = dataset_query['query']['source-table']
    elif data.get('result_metadata'):
        table_id = data['result_metadata'][0].get('table_id')

    # Native SQL query
    if dataset_query.get('type') == 'native':
        sql_query = dataset_query.get('native', {}).get('query', '')
        table_name = extract_table_from_sql(sql_query)

    print(f"📋 Table ID       : {table_id or 'N/A'}")
    print(f"📋 Table Name     : {table_name or 'N/A'}")

    # ---- Other Info ----
    dashboard = data.get('dashboard') or {}
    creator = data.get('creator') or {}

    print(f"📊 Display Type   : {data.get('display')}")
    print(f"📁 Dashboard      : {dashboard.get('name', 'N/A')} (ID: {dashboard.get('id', 'N/A')})")
    print(f"👤 Creator        : {creator.get('first_name', 'Unknown')} {creator.get('last_name', '')}".strip())
    print(f"👁️ View Count     : {data.get('view_count', 0)}")
    print(f"🕒 Created At     : {format_time(data.get('created_at'))}")
    print(f"🔄 Updated At     : {format_time(data.get('updated_at'))}")
    print(f"📅 Last Used At   : {format_time(data.get('last_used_at'))}")
    print(f"📈 Avg Query Time : {data.get('average_query_time', 'N/A')} ms")
    print(f"⚙️ Can Write      : {icon_bool(data.get('can_write'))}")
    print(f"⚙️ Can Delete     : {icon_bool(data.get('can_delete'))}")
    print(f"⚙️ Can Restore    : {icon_bool(data.get('can_restore'))}")
    print(f"🗃️ Archived       : {icon_bool(data.get('archived'))}")

    # ---- Result Metadata ----
    result_metadata = data.get('result_metadata') or []
    print(f'\n📋 Result Metadata ({len(result_metadata)} fields):')

    if not result_metadata:
        print('   • No metadata.')
    else:
        for i, field in enumerate(result_metadata, 1):
            name = field.get('name')
            base_type = field.get('base_type')
            display_name = field.get('display_name')
            fingerprint = field.get('fingerprint', {}).get('global', {})
            distinct_count = fingerprint.get('distinct-count', 'N/A')
            nil_pct = fingerprint.get('nil%', 'N/A')

            print(f'   {i}. {display_name} ({name}) - Type: {base_type}')
            print(f'       - Distinct Count: {distinct_count}')
            print(f'       - Nil %        : {nil_pct}')

    # ---- Query ----
    native_query = dataset_query.get('native', {}).get('query', 'N/A')
    print(f'\n🔍 Query:\n{native_query}')

    print('=' * 60)
