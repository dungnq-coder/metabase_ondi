"""Interactive menu for Metabase permissions groups."""

from __future__ import annotations

import json
from typing import Any

from src.connector.manager import MetabaseAPIManager
from src.menu_cli._base import confirm_and_delete, run_resource_menu
from src.utils.input_utils import input_int, input_str
from src.utils.print_permissions import (
    print_db_permission_detail,
    print_group_members_tree,
    print_groups_list,
    print_permissions_list,
)
from src.utils.screen_contact import clear_screen

PERMISSION_OPTIONS: dict[str, list[str]] = {
    'view-data': ['blocked', 'restricted', 'unrestricted'],
    'create-queries': ['none', 'query-builder', 'query-builder-and-native'],
    'download': ['none', 'schemas:full'],
    'data-model': ['none', 'schemas:all'],
    'details': ['no', 'yes'],
}


def _assign_member_to_group(
    manager: MetabaseAPIManager, group_id: int, user_id: int, is_group_manager: bool = False
) -> None:
    payload = {
        'group_id': group_id,
        'is_group_manager': is_group_manager,
        'user_id': user_id,
    }
    res = manager.permissions.post_permissions_action(action='membership', payload=payload)
    if res.status_code < 400:
        print(f'Add user {user_id} into group {group_id} successfully!')
    else:
        print(f'FAILED to add user {user_id} into group {group_id}.')


def _edit_permissions(current: dict[str, Any]) -> dict[str, Any]:
    new_permissions: dict[str, Any] = {}
    for key, value in current.items():
        print(f"\nPermission: '{key}' (current: {json.dumps(value, ensure_ascii=False)})")
        options = PERMISSION_OPTIONS.get(key)
        if options is None:
            print('⚠️ Unknown permission type — keeping current value.')
            new_permissions[key] = value
            continue
        print(f'Available options: {", ".join(options)}')
        new_val = input_str('Enter new value (or leave blank to keep current): ', required=False)
        if not new_val or new_val not in options:
            if new_val:
                print('⚠️ Invalid option. Keeping current value.')
            new_permissions[key] = value
        elif key in {'download', 'data-model'}:
            new_permissions[key] = {'schemas': new_val.split(':')[-1]}
        else:
            new_permissions[key] = new_val
    return new_permissions


def _assign_permissions_to_dbs(
    manager: MetabaseAPIManager,
    group_id: str,
    template_dbs: dict[str, Any],
    present_permission: dict[str, Any],
) -> dict[str, Any]:
    if not template_dbs:
        print('⚠️ No template databases found. Cannot proceed.')
        return {}

    print('\n=== Available Databases ===')
    for db_id in template_dbs:
        print(f'- Database ID: {db_id}')

    raw = (
        input_str(
            '\nEnter one or more database_id to add/update permissions (comma separated): ',
            required=True,
        )
        or ''
    )
    db_ids = [x.strip() for x in raw.split(',') if x.strip() in template_dbs]
    if not db_ids:
        print('❌ No valid database IDs selected. Cancelled.')
        return {}

    new_group_permissions = {db_id: _edit_permissions(template_dbs[db_id]) for db_id in db_ids}
    present_permission['groups'][group_id] = new_group_permissions
    response = manager.permissions.update_premissions(payload=present_permission)
    if response.status_code < 400:
        print(f'✅ Permissions for group {group_id} updated successfully.')
    else:
        print(f'❌ Failed to update permissions. Status code: {response.status_code}')
    return new_group_permissions


def _list_permissions_groups(manager: MetabaseAPIManager) -> None:
    permissions = manager.permissions.get_permissions_detail(extra='group').json()
    clear_screen()
    print_groups_list(permissions)


def _view_permissions_details(manager: MetabaseAPIManager) -> None:
    permissions = manager.permissions.get_permissions_detail(extra='graph').json()
    clear_screen()
    print_permissions_list(permissions)
    pid = input_int('Enter PermissionID to view details (or q to cancel): ')
    if pid:
        _view_permissions_by_id(manager, pid)
    else:
        input('🔙 Press Enter to return...')


def _view_permissions_by_id(manager: MetabaseAPIManager, pid: int) -> None:
    extra = input('Which object id? (group / database): ').strip().lower()
    if extra == 'group':
        permissions = manager.permissions.get_permissions_detail(extra='group', group_id=pid)
        clear_screen()
        print_group_members_tree(permissions.json())
    elif extra == 'database':
        permissions = manager.permissions.get_permissions_detail(extra='graph/db', database_id=pid)
        clear_screen()
        print_db_permission_detail(permissions.json())
    else:
        print('❌ Invalid type. Returning.')
    input('🔙 Press Enter to return...')


def _create_permissions(manager: MetabaseAPIManager) -> None:
    clear_screen()
    print('🆕 Create a new permissions group')

    name = input_str('Enter permissions group name: ', required=True)
    res = manager.permissions.post_permissions_action(action='group', payload={'name': name})
    if res.status_code >= 400:
        print(f"❌ Failed to create group '{name}' (status {res.status_code})")
        input('🔙 Press Enter to return...')
        return

    new_group_id = str(res.json().get('id'))
    if not new_group_id:
        print('❌ Could not retrieve new group ID.')
        input('🔙 Press Enter to return...')
        return

    present_permission = manager.permissions.get_permissions_detail(extra='graph').json()
    admin_dbs = present_permission['groups'].get('2', {})
    if not admin_dbs:
        print('⚠️ Administrator group has no databases. Cannot proceed.')
        input('🔙 Press Enter to return...')
        return

    _assign_permissions_to_dbs(manager, new_group_id, admin_dbs, present_permission)

    all_member = manager.permissions.get_permissions_detail(extra='group', group_id=1)
    print('Current all member: ')
    print_group_members_tree(all_member.json())
    members = input(
        'Enter user_id to add permissions (comma separated, leave blank to skip): '
    ).strip()
    if members:
        for u in members.split(','):
            u = u.strip()
            if u.isdigit():
                _assign_member_to_group(manager, int(new_group_id), int(u))
            else:
                print(f"⚠️ Invalid user ID '{u}' skipped.")

    input('🔙 Press Enter to return...')


def _update_permissions(manager: MetabaseAPIManager) -> None:
    present_permission = manager.permissions.get_permissions_detail(extra='graph').json()
    groups = present_permission.get('groups', {})
    if not groups:
        print('⚠️  No group permissions found.')
        input('🔙 Press Enter to return...')
        return

    print('\n=== Available Groups ===')
    for gid in groups:
        print(f'- Group ID: {gid}')
    gid = input_str("\nEnter group_id to update (or 'q' to cancel): ")
    if not gid or gid not in groups:
        print('❌ Invalid group ID. Operation cancelled.')
        input('🔙 Press Enter to return...')
        return
    print(f'\n--- Updating permissions for group {gid} ---')
    _assign_permissions_to_dbs(manager, gid, groups[gid], present_permission)
    input('🔙 Press Enter to return...')


def _delete_permissions(manager: MetabaseAPIManager) -> None:
    did = input_int("Enter permissions group ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return
    confirm_and_delete('permissions group', did, manager.permissions.delete_specific_permissions)


def _user_permissions_actions(manager: MetabaseAPIManager) -> None:
    while True:
        clear_screen()
        all_member = manager.permissions.get_permissions_detail(extra='group', group_id=1)
        print('Current all member: ')
        print_group_members_tree(all_member.json())
        print('-' * 100)
        print('List all groups: ')
        permissions = manager.permissions.get_permissions_detail(extra='group').json()
        print_groups_list(permissions)
        print('-' * 100)

        print('Actions:\n  [a] Add users to group\n  [d] Remove users from group\n  [q] Cancel')
        action = input('Enter choice: ').strip().lower()

        if action == 'a':
            group_id = input_int('Enter group id: ')
            user_ids_str = (
                input_str('Enter user ids comma-separated (blank to return): ', required=False)
                or ''
            )
            for u in user_ids_str.split(','):
                u = u.strip()
                if u.isdigit() and group_id is not None:
                    _assign_member_to_group(manager, group_id, int(u))
                elif u:
                    print(f"⚠️ Invalid user ID '{u}' skipped.")
        elif action == 'd':
            print('Function in development!')
            input('Press any key to return!')
        elif action == 'q':
            break


def permissions_menu(manager: MetabaseAPIManager) -> None:
    run_resource_menu(
        title='Permissions',
        list_fn=lambda: _list_permissions_groups(manager),
        actions={
            'm': ('View permissions details', lambda: _view_permissions_details(manager)),
            'c': ('Create new permissions group', lambda: _create_permissions(manager)),
            'u': ('Update permissions', lambda: _update_permissions(manager)),
            'd': ('Delete permissions', lambda: _delete_permissions(manager)),
            'a': ('Add/delete user in group', lambda: _user_permissions_actions(manager)),
        },
        id_handler=lambda pid: _view_permissions_by_id(manager, pid),
    )
