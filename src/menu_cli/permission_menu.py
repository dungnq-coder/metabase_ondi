import json

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.print_permissions import *
from src.utils.screen_contact import clear_screen


def list_permissions_group(manager: MetabaseAPIManager):
    permissions = manager.permissions.get_permissions_detail(
        extra='group').json()
    clear_screen()
    print_groups_list(permissions)


def view_permissions_details(manager: MetabaseAPIManager):
    permissions = manager.permissions.get_permissions_detail(
        extra='graph').json()
    clear_screen()
    print_permissions_list(permissions)

    pid = input_int(
        'Do you want to view detail permission id? Enter PermissionID to view or q to cancel: '
    )
    if pid:
        view_permissions_by_id(manager=manager, pid=pid)
    else:
        input('🔙 Press Enter to return...')


def view_permissions_by_id(manager: MetabaseAPIManager, pid: int):
    extra = input('Which object id you just provide? (group or database): '
                  ).strip().lower()

    if extra == 'group':
        permissions = manager.permissions.get_permissions_detail(extra='group',
                                                                 group_id=pid)
        clear_screen()
        print_group_members_tree(permissions.json())
    elif extra == 'database':
        permissions = manager.permissions.get_permissions_detail(
            extra='graph/db', database_id=pid)
        clear_screen()
        print_db_permission_detail(permissions.json())
    else:
        print('❌ Invalid type. Returning.')

    input('🔙 Press Enter to return...')


def edit_permissions(current_permissions: dict) -> dict:
    """
    Hiển thị và chỉnh sửa quyền từ current_permissions.
    Trả về dict quyền mới.
    """
    new_permissions = {}

    for key, value in current_permissions.items():
        print(
            f"\nPermission: '{key}' (current: {json.dumps(value, ensure_ascii=False)})"
        )

        if key == 'view-data':
            options = ['blocked', 'restricted', 'unrestricted']
        elif key == 'create-queries':
            options = ['none', 'query-builder', 'query-builder-and-native']
        elif key == 'download':
            options = ['none', 'schemas:full']
        elif key == 'data-model':
            options = ['none', 'schemas:all']
        elif key == 'details':
            options = ['no', 'yes']
        else:
            print('⚠️ Unknown permission type — keeping current value.')
            new_permissions[key] = value
            continue

        print(f"Available options: {', '.join(options)}")
        new_val = input_str(
            'Enter new value (or leave blank to keep current): ',
            required=False)

        if not new_val or new_val not in options:
            if new_val:
                print('⚠️ Invalid option. Keeping current value.')
            new_permissions[key] = value
        else:
            # Chuyển dạng {'schemas': 'full'} cho download/data-model
            if key in ['download', 'data-model']:
                schema_val = new_val.split(':')[-1]
                new_permissions[key] = {'schemas': schema_val}
            else:
                new_permissions[key] = new_val

    return new_permissions


def create_permissions(manager: MetabaseAPIManager):
    clear_screen()
    print('🆕 Create a new permissions group')
    name = input_str('Enter permissions group name: ', required=True)

    # --- Tạo group mới ---
    res = manager.permissions.post_permissions_action(action='group',
                                                      payload={'name': name})
    if res.status_code >= 400:
        print(f"❌ Failed to create group '{name}' (status {res.status_code})")
        input('Press Enter to return...')
        return

    new_group_id = str(res.json().get('id'))
    if not new_group_id:
        print('❌ Could not retrieve new group ID. Operation cancelled.')
        input('Press Enter to return...')
        return

    # --- Lấy template DB từ Admin group ---
    present_permission = manager.permissions.get_permissions_detail(
        extra='graph').json()
    admin_dbs = present_permission['groups'].get('2', {})
    if not admin_dbs:
        print('⚠️ Administrator group has no databases. Cannot proceed.')
        input('🔙 Press Enter to return...')
        return

    print('\n=== Available Databases ===')
    for db_id in admin_dbs:
        print(f'- Database ID: {db_id}')

    db_ids_input = input_str(
        '\nEnter one or more database_id to add permissions (comma separated): ',
        required=True)
    db_ids = [
        x.strip() for x in db_ids_input.split(',') if x.strip() in admin_dbs
    ]
    if not db_ids:
        print('❌ No valid database IDs selected. Cancelled.')
        input('🔙 Press Enter to return...')
        return

    # --- Chỉnh quyền cho từng database ---
    new_group_permissions = {
        db_id: edit_permissions(admin_dbs[db_id])
        for db_id in db_ids
    }

    # --- Cập nhật payload và tạo permissions ---
    present_permission['groups'][new_group_id] = new_group_permissions
    response = manager.permissions.update_premissions(
        payload=present_permission)
    if response.status_code < 400:
        print(f'✅ Permissions group "{name}" created successfully.')
    else:
        print(
            f'❌ Failed to create permissions. Status code: {response.status_code}'
        )

    input('🔙 Press Enter to return...')


def update_permissions(manager: MetabaseAPIManager):
    present_permission = manager.permissions.get_permissions_detail(
        extra='graph').json()
    groups = present_permission.get('groups', {})

    if not groups:
        print('⚠️  No group permissions found.')
        input('🔙 Press Enter to return...')
        return

    print('\n=== Available Groups ===')
    for gid in groups.keys():
        print(f'- Group ID: {gid}')
    gid = input_str("\nEnter group_id to update (or 'q' to cancel): ")

    if gid not in groups:
        print('❌ Invalid group ID. Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    dbs = groups[gid]
    print('\n=== Databases for this group ===')
    for db_id in dbs.keys():
        print(f'- Database ID: {db_id}')

    db_ids_input = input_str(
        '\nEnter one or more database_id (comma separated): ')
    if not db_ids_input:
        print('❌ No database selected. Cancelled.')
        input('🔙 Press Enter to return...')
        return

    db_ids = [x.strip() for x in db_ids_input.split(',') if x.strip() in dbs]
    if not db_ids:
        print('❌ No valid database IDs selected. Cancelled.')
        input('🔙 Press Enter to return...')
        return

    for db_id in db_ids:
        print(f'\n=== Updating permissions for Database {db_id} ===')
        dbs[db_id] = edit_permissions(dbs[db_id])

    present_permission['groups'][gid] = dbs
    response = manager.permissions.update_premissions(
        payload=present_permission)

    if response.status_code < 400:
        print('✅ Permissions updated successfully.')
    else:
        print(
            f'❌ Failed to update permissions. Status code: {response.status_code}'
        )

    input('🔙 Press Enter to return...')


def delete_permissions(manager: MetabaseAPIManager):
    did = input_int(
        "Enter permissions group ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(
        f'Are you sure you want to delete permissions group ID {did}?')
    if confirm:
        res = manager.permissions.delete_specific_permissions(did)
        if res.status_code < 400:
            print(f'✅ Permissions ID {did} deleted successfully.')
        else:
            print(
                f'❌ Failed to delete permissions ID {did}. Status code: {res.status_code}'
            )
    else:
        print('Delete cancelled.')

    input('🔙 Press Enter to return...')


def permissions_menu(manager: MetabaseAPIManager):
    while True:
        list_permissions_group(manager)

        print('\nOptions:')
        print('  [id] - View permissions by ID')
        print('  m    - View permissions details')
        print('  c    - Create new permissions group')
        print('  u    - Update permissions')
        print('  d    - Delete permissions')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip().lower()

        if action == 'b':
            break
        elif action == 'c':
            create_permissions(manager)
        elif action == 'm':
            view_permissions_details(manager)
        elif action == 'u':
            update_permissions(manager)
        elif action == 'd':
            delete_permissions(manager)
        elif action.isdigit():
            view_permissions_by_id(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
