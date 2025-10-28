from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.print_collections import *
from src.utils.screen_contact import clear_screen


def list_collections(manager: MetabaseAPIManager):
    """
    Display all collections in a tree structure.

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    collections = manager.collection.list_all_collections_in_tree()
    clear_screen()
    print('📁 All Collections')
    print('=' * 60)
    print_collection_tree(collections)
    print('=' * 60)


def view_collection_details(manager: MetabaseAPIManager):
    """
    Display a flat list of all collections with basic information.

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    clear_screen()
    print('Collection List:')
    print_collections(manager.collection.list__all_collections())
    input('🔙 Press Enter to return...')


def create_collection(manager: MetabaseAPIManager):
    """
    Create a new collection (currently placeholder).

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    clear_screen()
    print('🔧 Create collection → Function in development')
    input('🔙 Press Enter to return...')


def update_collection(manager: MetabaseAPIManager):
    """
    Update information of an existing collection (currently placeholder).

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    cid = input_int("Enter collection ID to update (or 'q' to cancel): ")
    if cid is None:
        print('Update collection cancelled.')
    else:
        print(f'🔧 Update collection {cid} → Function in development')
    input('🔙 Press Enter to return...')


def delete_collection(manager: MetabaseAPIManager):
    """
    Delete a specific collection by ID.

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    cid = input_int("Enter collection ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete collection cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirmed = input_yes_no(
        f'Are you sure you want to delete collection ID {cid}?')
    if confirmed:
        res = manager.collection.delete_specific_collection(cid)
        if res.status_code < 400:
            print(f'✅ Collection ID {cid} deleted successfully.')
        else:
            print(
                f'❌ Failed to delete collection ID {cid}. Status code: {res.status_code}'
            )
    else:
        print('Delete collection cancelled.')

    input('🔙 Press Enter to return...')


def view_collection_items(manager: MetabaseAPIManager, cid: int):
    """
    View details and contained items of a specific collection.

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
        cid (int): The collection ID to view.
    """
    try:
        col = manager.collection.get_specific_collection(cid)
        clear_screen()
        print_collection_info(col)
        view_item = input_str(
            'Press y to view items in this collection, any other key to return: ',
            required=False,
            allow_cancel=False)
        if view_item and view_item.lower() == 'y':
            items = manager.collection.get_colletion_detail(collection_id=cid,
                                                            extra='items')
            print_collection_items(items)
            input('🔙 Press Enter to return...')
    except Exception as e:
        print(f'❌ Error: Could not retrieve collection ID {cid}. ({e})')
        input('🔙 Press Enter to exit...')


def collection_menu(manager: MetabaseAPIManager):
    """
    Display the main interactive menu for managing Metabase collections.

    This function allows the user to:
    - View all collections
    - Create a new collection
    - Update an existing collection
    - Delete a collection
    - View items inside a specific collection

    Args:
        manager (MetabaseAPIManager): The Metabase API manager instance.
    """
    while True:
        list_collections(manager)

        print('\nOptions:')
        print('  [id] - View items in collection by ID')
        print('  m    - View collection details')
        print('  c    - Create new collection')
        print('  u    - Update collection')
        print('  d    - Delete collection')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'm':
            view_collection_details(manager)
        elif action.lower() == 'c':
            create_collection(manager)
        elif action.lower() == 'u':
            update_collection(manager)
        elif action.lower() == 'd':
            delete_collection(manager)
        elif action.isdigit():
            view_collection_items(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
