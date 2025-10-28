import json
from pathlib import Path
from pprint import pprint

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.print_permissions import *
from src.utils.screen_contact import clear_screen


def list_permissions_group(manager: MetabaseAPIManager):
    permissionss = manager.permissions.get_permissions_detail(extra='group').json()
    clear_screen()
    print_groups_list(permissionss)


def view_permissions_details(manager: MetabaseAPIManager):
    permissionss = manager.permissions.get_permissions_detail(extra='graph').json()
    clear_screen()
    print_permissions_list(permissionss)

    pid = input_int('Do you want to view detail permission id? Enter PermissionID to view or q to cancel: ')
    if pid:
        view_permissions_by_id(manager=manager, pid=pid)
    else: input('🔙 Press Enter to return...')

def view_permissions_by_id(manager: MetabaseAPIManager, pid: int):
    extra = input('Which object id you just provide?(group or database): ')
    if extra == 'group':
        permissions = manager.permissions.get_permissions_detail(extra='group', group_id=pid)
        clear_screen()
        print_group_members_tree(permissions.json())
        input('🔙 Press Enter to return...')


def create_permissions(manager: MetabaseAPIManager):
    clear_screen()
    print('🆕 Create a new permissions connection')

    name = input_str('Enter permissions name: ', required=True)

    input('🔙 Press Enter to return...')


def update_permissions(manager: MetabaseAPIManager):
    pid = input_int("Enter permissions ID to update (or 'q' to cancel): ")
    if pid is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    response = None
    if response.status_code < 400:
        print(f'permissions ID {pid} updated successfully.')
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
