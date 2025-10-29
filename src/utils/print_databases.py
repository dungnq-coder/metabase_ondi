# src/utils/print_databases.py
from .format_time import format_time
from .icons import icon_bool


def print_databases_list(data: dict):
    """
    In danh sách databases từ Metabase API một cách gọn gàng, dễ đọc.
    """
    if not data or 'data' not in data:
        print('❗ Không có dữ liệu database.')
        return

    databases = data.get('data', [])
    total = data.get('total', len(databases))
    print(f'\n🗄️  Databases (Total: {total})\n')

    for i, db in enumerate(databases, start=1):
        prefix = '└──' if i == len(databases) else '├──'

        print(f"{prefix} {db.get('name', 'Unknown')} [ID: {db.get('id')}]")
        print(f"    ├── Engine        : {db.get('engine', 'N/A')}")
        print(f"    ├── Timezone      : {db.get('timezone', 'N/A')}")
        print(
            f"    ├── Auto Run Query: {icon_bool(db.get('auto_run_queries'))}")
        print(f"    ├── Full Sync     : {icon_bool(db.get('is_full_sync'))}")
        print(
            f"    ├── Upload Enabled: {icon_bool(db.get('uploads_enabled'))}")
        print(f"    ├── Sample DB     : {icon_bool(db.get('is_sample'))}")
        print(
            f"    ├── Permissions   : {db.get('native_permissions', 'N/A').capitalize()}"
        )
        print(f"    ├── Created At    : {format_time(db.get('created_at'))}")
        print(f"    ├── Updated At    : {format_time(db.get('updated_at'))}")
        print(
            f"    ├── Sync Schedule : {db.get('metadata_sync_schedule', '—')}")
        print(
            f"    ├── Cache Refresh : {db.get('cache_field_values_schedule', '—')}"
        )
        print(
            f"    └── Features      : {len(db.get('features', []))} supported\n"
        )


def print_database_details(db: dict):
    """
    In chi tiết 1 database Metabase ra CLI — gọn, dễ đọc, vẫn đủ thông tin để thao tác.
    """
    if not db:
        print('❗ Database data is empty.')
        return

    print('\nDatabase Details')
    print('=' * 60)

    print(f"🆔 ID              : {db.get('id')}")
    print(f"📛 Name            : {db.get('name')}")
    print(f"🗄️  Engine          : {db.get('engine', 'N/A')}")
    print(f"🌍 Timezone        : {db.get('timezone', 'N/A')}")
    print(f"👤 Creator ID      : {db.get('creator_id', '—')}")
    print(f"📦 Sample Database : {icon_bool(db.get('is_sample'))}")
    print(f"📤 Upload Enabled  : {icon_bool(db.get('uploads_enabled'))}")
    print(f"⚙️  Auto Run Query  : {icon_bool(db.get('auto_run_queries'))}")
    print(f"🔁 Full Sync        : {icon_bool(db.get('is_full_sync'))}")
    print(f"🧱 Audit DB         : {icon_bool(db.get('is_audit'))}")
    print(f"🧩 On Demand        : {icon_bool(db.get('is_on_demand'))}")
    print(f"🕒 Created At       : {format_time(db.get('created_at'))}")
    print(f"🔄 Updated At       : {format_time(db.get('updated_at'))}")
    print(f"📈 Initial Sync     : {db.get('initial_sync_status', 'N/A')}")

    # --- Schedules ---
    print('\n⏰ Sync Schedules:')
    schedules = db.get('schedules', {})
    if not schedules:
        print('   • No schedule info available.')
    else:
        metadata = schedules.get('metadata_sync', {})
        cache = schedules.get('cache_field_values', {})
        print(
            f"   • Metadata Sync : type={metadata.get('schedule_type')} | minute={metadata.get('schedule_minute')} | hour={metadata.get('schedule_hour', '—')}"
        )
        print(
            f"   • Cache Refresh : type={cache.get('schedule_type')} | minute={cache.get('schedule_minute')} | hour={cache.get('schedule_hour', '—')}"
        )

    # --- Features ---
    features = db.get('features', []) or []
    print(f'\n🧰 Supported Features ({len(features)}):')
    if not features:
        print('   • No features listed.')
    else:
        # In 3 cột để gọn
        cols = 3
        for i in range(0, len(features), cols):
            chunk = features[i:i + cols]
            print('   ' + ' | '.join(f'{f}' for f in chunk))

    # --- Optional fields ---
    if db.get('description'):
        print(f"\n📝 Description:\n   {db['description']}")
    if db.get('caveats'):
        print(f"\n⚠️  Caveats:\n   {db['caveats']}")
    if db.get('points_of_interest'):
        print(f"\n📍 Points of Interest:\n   {db['points_of_interest']}")

    print('=' * 60)


def print_database_summary(db):
    """
    Nicely print a concise summary of a database JSON response
    in a clean, human-readable CLI format (similar to other print_ functions).

    Supports both raw JSON strings and Python dicts.
    Automatically hides null or overly verbose fields.
    """

    if not isinstance(db, dict):
        print('⚠️  Unsupported response type.')
        return

    print('\n🧾 Database Summary')
    print('=' * 60)

    # --- Basic Info ---
    print(f"🆔 ID              : {db.get('id', '—')}")
    print(f"📛 Name            : {db.get('name', '—')}")
    print(f"🗄️  Engine          : {db.get('engine', '—')}")
    print(f"👤 Creator ID      : {db.get('creator_id', '—')}")
    print(f"🌍 Timezone        : {db.get('timezone', '—')}")
    print(
        f"⚙️  Auto Run Query  : {'✅' if db.get('auto_run_queries') else '❌'}")
    print(f"🔁 Full Sync        : {'✅' if db.get('is_full_sync') else '❌'}")
    print(f"📦 Upload Enabled  : {'✅' if db.get('uploads_enabled') else '❌'}")
    print(f"🧱 Audit DB         : {'✅' if db.get('is_audit') else '❌'}")
    print(f"🧩 On Demand        : {'✅' if db.get('is_on_demand') else '❌'}")
    print(f"🕒 Created At       : {db.get('created_at', '—')}")
    print(f"🔄 Updated At       : {db.get('updated_at', '—')}")
    print(f"📈 Initial Sync     : {db.get('initial_sync_status', '—')}")
    print(f"🧭 Engine Version   : {db.get('dbms_version', '—')}")

    # --- Features ---
    features = db.get('features', []) or []
    print(f'\n🧰 Supported Features ({len(features)}):')
    if features:
        preview = ', '.join(features[:5])
        if len(features) > 5:
            preview += f' ... (+{len(features) - 5} more)'
        print(f'   {preview}')
    else:
        print('   • None listed')

    # --- Details ---
    details = db.get('details', {})
    if details:
        print('\n📋 Details:')
        for k, v in details.items():
            if 'service-account' in k:
                print(f'   • {k}: [hidden]')
            else:
                print(f'   • {k}: {v}')

    # --- Schedules ---
    print('\n⏰ Sync Schedules:')
    print(f"   • Metadata Sync : {db.get('metadata_sync_schedule', '—')}")
    print(f"   • Cache Refresh : {db.get('cache_field_values_schedule', '—')}")

    print('=' * 60)
