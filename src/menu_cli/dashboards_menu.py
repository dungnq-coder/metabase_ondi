from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.process_response_data import *
from src.utils.screen_contact import clear_screen


def list_dashboards(manager: MetabaseAPIManager):
    dashboards = manager.dashboard.list_all_dashboards()
    clear_screen()
    print('📊 All Dashboards')
    print('=' * 60)
    print_dashboard_list(dashboards)


def view_dashboard(manager: MetabaseAPIManager, did: int):
    dash = manager.dashboard.get_dashboard_detail(did)
    clear_screen()
    print_dashboard_details(dash)
    input('🔙 Press Enter to return...')


def create_dashboard(manager: MetabaseAPIManager):
    action = input_str(
        "Enter dashboard template id to create a copy dashboard or press Enter to create a new dashboard (or 'q' to cancel): ",
        required=False,
        allow_cancel=True)
    if action is None:
        print('Operation cancelled.')
        input('🔙 Press Enter to return...')
        return

    if action.isdigit():
        collection_id = input_str(
            "Enter collection ID to place the copied dashboard (or press Enter to skip, 'q' to cancel): ",
            required=False,
            allow_cancel=True)
        if collection_id == 'q':
            print('Operation cancelled.')
            input('🔙 Press Enter to return...')
            return

        name = input_str(
            "Enter name for the copied dashboard (or 'q' to cancel): ",
            required=True,
            allow_cancel=True)
        if name is None:
            print('Operation cancelled.')
            input('🔙 Press Enter to return...')
            return

        order = input_str(
            "Specific position in collection (or press Enter to skip, 'q' to cancel): ",
            required=False,
            allow_cancel=True)
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
            collection_id=int(collection_id)
            if collection_id and collection_id.isdigit() else None,
            collection_position=int(order)
            if order and order.isdigit() else None,
            is_deep_copy=is_deep_copy,
            name=name)
        result = manager.dashboard.post_dashboard_action(
            dashboard_id=int(action), action='copy', payload=payload)
        print_dashboard_copy_result(result)
        input('🔙 Press Enter to return...')
    else:
        print('🔧 Create dashboard → Function in development')
        input('🔙 Press Enter to return...')


def update_dashboard(manager: MetabaseAPIManager):
    did = input_int("Enter dashboard ID to update (or 'q' to cancel): ")
    if did is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    print(f'🔧 Update dashboard {did} → Function in development')
    input('🔙 Press Enter to return...')


def delete_dashboard(manager: MetabaseAPIManager):
    did = input_int("Enter dashboard ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(
        f'Are you sure you want to delete dashboard ID {did}?')
    if confirm:
        res = manager.dashboard.delete_specific_dashboard(did)
        if res.status_code < 400:
            print(f'Dashboard ID {did} deleted successfully.')
        else:
            print(
                f'Failed to delete dashboard ID {did}. Status code: {res.status_code}'
            )
    else:
        print('Delete cancelled.')

    input('🔙 Press Enter to return...')


def dashboard_menu(manager: MetabaseAPIManager):
    while True:
        list_dashboards(manager)

        print('\nOptions:')
        print('  [id] - View dashboard by ID')
        print('  c    - Create new dashboard')
        print('  u    - Update dashboard')
        print('  d    - Delete dashboard')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'c':
            create_dashboard(manager)
        elif action.lower() == 'u':
            update_dashboard(manager)
        elif action.lower() == 'd':
            delete_dashboard(manager)
        elif action.isdigit():
            view_dashboard(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
