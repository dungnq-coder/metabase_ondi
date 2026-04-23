# src/utils/print_cards.py
from pprint import pprint
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
    print(data)
    if not data:
        print('❗ Data empty.')
        return
    
    pprint(data)

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
    if dataset_query.get('query', {}).get('source-query'):
        table_id = dataset_query['query']['source-query']['source-table']
    elif data.get('result_metadata'):
        table_id = data['result_metadata'][0].get('table_id')

    # Determine SQL: support top-level native and staged MBQL (stages)
    sql_query = None
    # top-level native (common shape)
    native = dataset_query.get('native')
    if native:
        sql_query = native.get('query') or native.get('native')
    else:
        # staged MBQL: look for a stage with native SQL
        stages = dataset_query.get('stages') or []
        for st in stages:
            if st.get('lib/type') == 'mbql.stage/native' or 'native' in st:
                sql_query = st.get('native') or st.get('query')
                break

    table_name = extract_table_from_sql(sql_query)

    print(f"📋 Table ID       : {table_id or 'N/A'}")
    print(f"📋 Table Name     : {table_name or 'N/A'}")

    # ---- Other Info ----
    dashboard = data.get('dashboard') or {}
    creator = data.get('creator') or {}

    print(f"📊 Display Type   : {data.get('display')}")
    print(
        f"📁 Dashboard      : {dashboard.get('name', 'N/A')} (ID: {dashboard.get('id', 'N/A')})"
    )
    print(
        f"👤 Creator        : {creator.get('first_name', 'Unknown')} {creator.get('last_name', '')}"
        .strip())
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
    display_sql = 'N/A'
    if sql_query:
        display_sql = sql_query
    else:
        # fallback: show top-level native if present
        if dataset_query.get('native'):
            nn = dataset_query.get('native')
            display_sql = nn.get('query') or nn.get('native') or 'N/A'
    print(f'\n🔍 Query:\n{display_sql}')

    print('=' * 60)
