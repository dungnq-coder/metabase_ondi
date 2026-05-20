"""Interactive menu for Metabase dashboards."""

from __future__ import annotations

from src.connector.manager import MetabaseAPIManager
from src.menu_cli._base import confirm_and_delete, run_resource_menu
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.print_dashboards import (
    print_dashboard_copy_result,
    print_dashboard_details,
    print_dashboard_list,
)
from src.utils.screen_contact import clear_screen


def _list_dashboards(manager: MetabaseAPIManager) -> None:
    dashboards = manager.dashboard.list_all_dashboards()
    clear_screen()
    print('📊 All Dashboards')
    print('=' * 60)
    print_dashboard_list(dashboards)


def _view_dashboard(manager: MetabaseAPIManager, did: int) -> None:
    dash = manager.dashboard.get_dashboard_detail(did)
    clear_screen()
    print_dashboard_details(dash)
    input('🔙 Press Enter to return...')


def _create_dashboard(manager: MetabaseAPIManager) -> None:
    action = input_str(
        'Enter dashboard template id to create a copy dashboard or press Enter '
        "to create a new dashboard (or 'q' to cancel): ",
        required=False,
        allow_cancel=True,
    )
    if action is None:
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    if not action.isdigit():
        print('🔧 Create dashboard → Function in development')
        input('🔙 Press Enter to return...')
        return

    collection_id = input_str(
        "Enter collection ID to place the copied dashboard (or press Enter to skip, 'q' to cancel): ",
        required=False,
        allow_cancel=True,
    )
    if collection_id == 'q':
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    name = input_str(
        "Enter name for the copied dashboard (or 'q' to cancel): ",
        required=True,
        allow_cancel=True,
    )
    if name is None:
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    order = input_str(
        "Specific position in collection (or press Enter to skip, 'q' to cancel): ",
        required=False,
        allow_cancel=True,
    )
    if order == 'q':
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    is_deep_copy = input_yes_no('Deep copy?', default=False)
    if is_deep_copy is None:
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    payload = manager.dashboard.get_copy_payload(
        collection_id=int(collection_id) if collection_id and collection_id.isdigit() else None,
        collection_position=int(order) if order and order.isdigit() else None,
        is_deep_copy=is_deep_copy,
        name=name,
    )
    result = manager.dashboard.post_dashboard_action(
        dashboard_id=int(action), action='copy', payload=payload
    )
    print_dashboard_copy_result(result)
    input('🔙 Press Enter to return...')


def _update_dashboard_placeholder() -> None:
    did = input_int("Enter dashboard ID to update (or 'q' to cancel): ")
    if did is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    print(f'🔧 Update dashboard {did} → Function in development')
    input('🔙 Press Enter to return...')


def _delete_dashboard(manager: MetabaseAPIManager) -> None:
    did = input_int("Enter dashboard ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return
    confirm_and_delete('dashboard', did, manager.dashboard.delete_specific_dashboard)


def dashboard_menu(manager: MetabaseAPIManager) -> None:
    run_resource_menu(
        title='Dashboards',
        list_fn=lambda: _list_dashboards(manager),
        actions={
            'c': ('Create new dashboard', lambda: _create_dashboard(manager)),
            'u': ('Update dashboard', _update_dashboard_placeholder),
            'd': ('Delete dashboard', lambda: _delete_dashboard(manager)),
        },
        id_handler=lambda did: _view_dashboard(manager, did),
    )
