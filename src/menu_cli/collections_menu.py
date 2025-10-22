from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.process_response_data import *
from src.utils.screen_contact import clear_screen


def collection_menu(manager: MetabaseAPIManager):

    def clear_and_list_collections():
        collections = manager.collection.list_all_collections_in_tree()
        clear_screen()
        print('📁 All Collections')
        print('=' * 60)
        print_collection_tree(collections)
        print('=' * 60)

    while True:
        clear_and_list_collections()

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
            clear_screen()
            print('Collection List:')
            print_collections(manager.collection.list__all_collections())
            input('🔙 Press Enter to return...')
        elif action.lower() == 'c':
            print('🔧 Create collection → Function in development')
            input('🔙 Press Enter to return...')
        elif action.lower() == 'u':
            cid = input_int(
                "Enter collection ID to update (or 'q' to cancel): ")
            if cid is None:
                print('Update collection cancelled.')
                input('🔙 Press Enter to return...')
                continue
            print(f'🔧 Update collection {cid} → Function in development')
            input('🔙 Press Enter to return...')
        elif action.lower() == 'd':
            cid = input_int(
                "Enter collection ID to delete (or 'q' to cancel): ")
            if cid is None:
                print('Delete collection cancelled.')
                input('🔙 Press Enter to return...')
                continue
            confirmed = input_yes_no(
                f'Are you sure you want to delete collection ID {cid}?')
            if confirmed:
                print(f'🔧 Delete collection {cid} → Function in development')
            else:
                print('Delete collection cancelled.')
            input('🔙 Press Enter to return...')
        elif action.isdigit():
            cid = int(action)
            col = manager.collection.get_specific_collection(cid)
            clear_screen()
            print_collection_info(col)
            view_item = input_str(
                'Press y to view items in this collection, any other key to return: ',
                required=False,
                allow_cancel=False)
            if view_item and view_item.lower() == 'y':
                items = manager.collection.get_items_in_a_specific_collection(
                    cid)
                print_collection_items(items)
                input('🔙 Press Enter to return...')
        else:
            input('❗ Invalid choice. Press Enter to continue.')
