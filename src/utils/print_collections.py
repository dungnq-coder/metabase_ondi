# src/utils/print_collections.py
from .icons import icon_bool, icon_model
from .format_time import format_time
from .permissions import format_permissions

# === Tất cả hàm về Collection ===
def print_collections(collections):
    if collections is None:
        print('❗ Collection empty.')
        return
    for col in collections:
        print(f"\n📁 [ID: {col['id']}] {col['name']}")
        print(f"    - Slug        : {col.get('slug')}")
        print(f"    - Path        : {col.get('location')}")

        personal = icon_bool(col.get('is_personal'))
        if col.get('is_personal') and col.get('personal_owner_id'):
            personal += f" (Owner ID: {col['personal_owner_id']})"
        print(f'    - Personal    : {personal}')

        print(f"    - Sample      : {icon_bool(col.get('is_sample'))}")

        if created := col.get('created_at'):
            print(f'    - Created At  : {created[:10]} GMT+0')

        if desc := col.get('description'):
            print(f'    - Description : {desc}')

        print(f"    - Write Access: {icon_bool(col.get('can_write'))}")


def print_collection_tree(collections, indent='', is_last=True):
    if collections is None:
        print('❗ Collection empty.')
        return
    for i, col in enumerate(collections):
        last = i == len(collections) - 1
        prefix = indent + ('└── ' if last else '├── ')

        tags = []
        if col.get('is_sample'):
            tags.append('🧪 Sample')
        if col.get('personal_owner_id'):
            tags.append('👤 Personal')
        if col.get('type') == 'trash':
            tags.append('🗑️ Trash')
        if col.get('here'):
            tags.append('📄 ' + ', '.join(col['here']))

        line = f"{col['name']} [ID: {col['id']}]"
        if tags:
            line += ' — ' + ' | '.join(tags)

        print(prefix + line)

        children = col.get('children', [])
        if children:
            next_indent = indent + ('    ' if last else '│   ')
            print_collection_tree(children, next_indent)


def print_collection_info(col):
    if col is None:
        print('❗ Collection empty.')
        return

    print(f"\n📁 Collection: {col['name']} (ID: {col['id']})")
    print(f"├── Slug         : {col.get('slug')}")
    print(f"├── Location     : {col.get('location')}")
    print(f"├── Parent ID    : {col.get('parent_id')}")
    print(f"├── Created At   : {col.get('created_at')}")
    print(f"├── Archived     : {icon_bool(col.get('archived'))}")
    print(f'├── Permissions  : {format_permissions(col)}')
    print(f"├── Personal     : {icon_bool(col.get('is_personal'))}")
    print(f"├── Sample       : {icon_bool(col.get('is_sample'))}")
    print(f"├── Namespace    : {col.get('namespace')}")
    print(f"├── Entity ID    : {col.get('entity_id')}")
    print(f'└── Ancestry     :')

    for i, anc in enumerate(col.get('effective_ancestors', [])):
        prefix = '    └── ' if i == len(
            col['effective_ancestors']) - 1 else '    📁 '
        print(f"{prefix}{anc['name']} (ID: {anc['id']})")


def print_collection_items(data):
    if data is None:
        print('❗ Collection empty.')
        return
    items = data.get('data', [])
    print(f'\n📦 Collection Items (Total: {len(items)})\n')

    for i, item in enumerate(items, start=1):
        model = item.get('model', 'unknown')
        icon = icon_model(model)
        name = item.get('name', 'Unnamed')
        print(f'{i}. {icon} [{model}] {name}')

        print(f"   ├── ID           : {item.get('id')}")
        print(f"   ├── Entity ID    : {item.get('entity_id')}")

        if db_id := item.get('database_id'):
            print(f'   ├── DB ID        : {db_id}')

        edit = item.get('last-edit-info', {})
        editor = f"{edit.get('first_name', '').strip()} {edit.get('last_name', '').strip()}"
        email = edit.get('email', 'unknown')
        print(
            f"   ├── Last Edit    : {editor} ({email}) at {format_time(edit.get('timestamp'))} GMT+0"
        )
        print(
            f"   ├── Last Used    : {format_time(item.get('last_used_at'))} GMT+0"
        )
        print(f'   ├── Permissions  : {format_permissions(item)}')
        print(
            f"   └── Archived     : {icon_bool(item.get('archived', False))}\n"
        )
