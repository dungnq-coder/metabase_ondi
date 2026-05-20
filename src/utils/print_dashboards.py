# src/utils/print_dashboards.py
from .format_time import format_time
from .icons import icon_bool, icon_display
from .permissions import format_permissions


# === Tất cả hàm về Dashboard ===
def print_dashboard_items(data: dict):
    items = data.get('data', [])
    print(f'\n📊 Dashboard Cards (Total: {len(items)})\n')

    for i, item in enumerate(items, start=1):
        name = item.get('name', 'Unnamed')
        display = item.get('display')
        icon = icon_display(display)
        dashboard = item.get('dashboard', {})
        dashboard_name = dashboard.get('name', 'Unknown Dashboard')
        dashboard_id = dashboard.get('id')

        print(f'{i}. {icon} [{display}] {name}')
        print(f'   ├── ID           : {item.get("id")} (Entity: {item.get("entity_id")})')
        print(f'   ├── Dashboard    : {dashboard_name} (ID: {dashboard_id})')

        if db_id := item.get('database_id'):
            print(f'   ├── DB ID        : {db_id}')

        print(f'   ├── Last Used    : {format_time(item.get("last_used_at"))}')
        print(f'   ├── Permissions  : {format_permissions(item)}')
        print(f'   └── Archived     : {icon_bool(item.get("archived"))}\n')


def print_dashboard_copy_result(result: dict):
    print('\n✅ Dashboard copied successfully:')
    print(f'  - Name        : {result.get("name")}')
    print(f'  - ID          : {result.get("id")}')
    print(f'  - Entity ID   : {result.get("entity_id")}')
    print(f'  - Collection  : {result.get("collection_id")}')
    print(f'  - Created At  : {result.get("created_at")} GMT+0')


def print_dashboard_list(dashboards: list):
    if not dashboards:
        print('❗ No dashboards found.')
        return

    print(f'\n📊 All Dashboards (Total: {len(dashboards)})\n')

    for i, dash in enumerate(dashboards, start=1):
        is_last = i == len(dashboards)
        prefix = '└──' if is_last else '├──'

        print(f'{prefix} 📊 Dashboard: {dash.get("name")} (ID: {dash.get("id")})')
        print(f'    ├── Views         : {dash.get("view_count", 0)}')
        print(
            f'    ├── Creator       : {dash.get("creator", {}).get("first_name", "Unknown")} (ID: {dash.get("creator_id")})'
        )
        print(f'    ├── Collection ID : {dash.get("collection_id", "-")}')
        print(f'    ├── Archived      : {icon_bool(dash.get("archived"))}')
        print(f'    ├── Public        : {icon_bool(bool(dash.get("public_uuid")))}')
        print(f'    ├── Width         : {dash.get("width", "-")}')
        print(
            f'    ├── Filters       : {"✅ Auto Apply" if dash.get("auto_apply_filters") else "❌ Manual"}'
        )
        print(f'    ├── Created At    : {format_time(dash.get("created_at"))} GMT+0')
        print(f'    └── Updated At    : {format_time(dash.get("updated_at"))} GMT+0\n')


def print_dashboard_details(data: dict):
    """
    Print general information about Dashboard Metabase on CLI.
    """
    if not data:
        print('❗ Dashboard data is empty.')
        return

    print('\n📊 Dashboard:', data.get('name', 'Unnamed Dashboard'))
    print('=' * 60)
    print(f'🆔 ID           : {data.get("id")} | Entity ID: {data.get("entity_id")}')
    print(f'📁 Collection   : {data.get("collection_id")}')
    print(f'👤 Creator      : {data.get("creator", {}).get("first_name", "Unknown")}')
    print(f'👀 Views        : {data.get("view_count", 0)}')
    print(f'🕒 Created At   : {format_time(data.get("created_at"))}')
    print(f'🔄 Updated At   : {format_time(data.get("updated_at"))}')
    print(f'💾 Archived     : {icon_bool(data.get("archived"))}')
    print(f'🛡️ Permissions  : {format_permissions(data)}')

    # --- Parameters ---
    parameters = data.get('parameters', [])
    print(f'\n⚙️ Parameters ({len(parameters)}):')
    if not parameters:
        print('   • Không có tham số.')
    else:
        for p in parameters:
            print(f'   • {p.get("name")} ({p.get("type")})')

    # --- Tabs ---
    tabs = data.get('tabs', [])
    print(f'\n🏷️ Tabs ({len(tabs)}):')
    if not tabs:
        print('   • Không có tab.')
    else:
        for tab in tabs:
            print(f'   • {tab.get("name")} (ID: {tab.get("id")})')

    # --- Cards ---
    dashcards = data.get('dashcards', [])
    print(f'\n📦 Cards ({len(dashcards)}):')
    if not dashcards:
        print('   • Không có card.')
    else:
        for i, dc in enumerate(dashcards, start=1):
            card = dc.get('card')
            if card and card.get('id'):
                name = card.get('name', 'Unnamed Card')
                display = card.get('display', 'text')
                icon = icon_display(display)
                card_id = card.get('id')
                database_id = card.get('database_id')
                print(
                    f'   {i}. {icon} {name} [ID: {card_id}] [Database ID: {database_id}] [{display}]\n'
                )
            else:
                # Text box
                text = dc.get('visualization_settings', {}).get('text', '[Text box]')
                entity_id = dc.get('entity_id', '—')
                text_preview = text[:40] + ('...' if len(text) > 40 else '')
                print(f'   {i}. 📝 Text Box [Entity ID: {entity_id}]: {text_preview}\n')

    print('=' * 60)
