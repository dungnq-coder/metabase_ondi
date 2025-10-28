import json
from pathlib import Path
from pprint import pprint

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.print_permissions import *
from src.utils.screen_contact import clear_screen


def list_permissions_group(manager: MetabaseAPIManager):
    permissionss = manager.permissions.get_permissions_detail(
        extra='group').json()
    clear_screen()
    print_groups_list(permissionss)


def view_permissions_details(manager: MetabaseAPIManager):
    permissionss = manager.permissions.get_permissions_detail(
        extra='graph').json()
    clear_screen()
    print_permissions_list(permissionss)

    pid = input_int(
        'Do you want to view detail permission id? Enter PermissionID to view or q to cancel: '
    )
    if pid:
        view_permissions_by_id(manager=manager, pid=pid)
    else:
        input('🔙 Press Enter to return...')


def view_permissions_by_id(manager: MetabaseAPIManager, pid: int):
    extra = input('Which object id you just provide?(group or database): ')
    if extra == 'group':
        permissions = manager.permissions.get_permissions_detail(extra='group',
                                                                 group_id=pid)
        clear_screen()
        print_group_members_tree(permissions.json())
        input('🔙 Press Enter to return...')

    if extra == 'database':
        permissions = manager.permissions.get_permissions_detail(
            extra='graph/db', database_id=pid)
        clear_screen()
        print_db_permission_detail(permissions.json())
        input('🔙 Press Enter to return...')


def create_permissions(manager: MetabaseAPIManager):
    clear_screen()
    print('🆕 Create a new permissions connection')

    name = input_str('Enter permissions name: ', required=True)

    input('🔙 Press Enter to return...')


def update_permissions(manager: MetabaseAPIManager):
    present_permission = manager.permissions.get_permissions_detail(
        extra='graph').json()
    groups = present_permission.get('groups', {})

    if not groups:
        print('⚠️  No group permissions found.')
        return

    # --- Hiển thị danh sách group ---
    print('\n=== Available Groups ===')
    for gid in groups.keys():
        print(f'- Group ID: {gid}')
    gid = input_str("\nEnter group_id to update (or 'q' to cancel): ")

    if gid not in groups:
        print('❌ Invalid group ID. Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    # --- Lấy danh sách database_id của group ---
    dbs = groups[gid]
    print('\n=== Databases for this group ===')
    for db_id in dbs.keys():
        print(f'- Database ID: {db_id}')

    db_ids_input = input_str(
        '\nEnter one or more database_id (comma separated): ')
    if not db_ids_input:
        print('❌ No database selected. Cancelled.')
        return

    db_ids = [x.strip() for x in db_ids_input.split(',') if x.strip() in dbs]
    if not db_ids:
        print('❌ No valid database IDs selected.')
        return

    for db_id in db_ids:
        print(f'\n=== Updating permissions for Database {db_id} ===')
        current = dbs[db_id]
        print('📋 Current permissions:')
        for k, v in current.items():
            print(f'  - {k}: {json.dumps(v, ensure_ascii=False)}')

        new_permissions = {}
        for key, value in current.items():
            print(f"\nEditing permission: '{key}'")
            print(f'Current value: {json.dumps(value, ensure_ascii=False)}')

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

            if not new_val:
                new_permissions[key] = value
                continue

            if new_val not in options:
                print('⚠️ Invalid option. Keeping current value.')
                new_permissions[key] = value
            else:
                if key in ['download', 'data-model']:
                    schema_val = new_val.split(':')[-1]
                    new_permissions[key] = {'schemas': schema_val}
                else:
                    new_permissions[key] = new_val
        dbs[db_id] = new_permissions

    present_permission['groups'][gid] = dbs

    response = manager.permissions.update_premissions(
        payload=present_permission)
    if response.status_code < 400:
        print(f'Permissions updated successfully.')
    else:
        print(
            f'Failed to update permissions. Status code: {response.status_code}'
        )
    input('🔙 Press Enter to return...')


def delete_permissions(manager: MetabaseAPIManager):
    did = input_int("Enter permissions ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(
        f'Are you sure you want to delete permissions ID {did}?')
    if confirm:
        res = manager.permissions.delete_specific_permissions(did)
        if res.status_code < 400:
            print(f'permissions ID {did} deleted successfully.')
        else:
            print(
                f'Failed to delete permissions ID {did}. Status code: {res.status_code}'
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
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'c':
            create_permissions(manager)
        elif action.lower() == 'm':
            view_permissions_details(manager)
        elif action.lower() == 'u':
            update_permissions(manager)
        elif action.lower() == 'd':
            delete_permissions(manager)
        elif action.isdigit():
            view_permissions_by_id(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
