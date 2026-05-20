"""Interactive menu for Metabase collections."""

from __future__ import annotations

from src.connector.manager import MetabaseAPIManager
from src.menu_cli._base import confirm_and_delete, run_resource_menu
from src.utils.input_utils import input_int, input_str
from src.utils.print_collections import (
    print_collection_info,
    print_collection_items,
    print_collection_tree,
    print_collections,
)
from src.utils.screen_contact import clear_screen


def _list_collections(manager: MetabaseAPIManager) -> None:
    collections = manager.collection.list_all_collections_in_tree()
    clear_screen()
    print('📁 All Collections')
    print('=' * 60)
    print_collection_tree(collections)
    print('=' * 60)


def _view_collection_details(manager: MetabaseAPIManager) -> None:
    clear_screen()
    print('Collection List:')
    print_collections(manager.collection.list__all_collections())
    input('🔙 Press Enter to return...')


def _create_collection_placeholder() -> None:
    clear_screen()
    print('🔧 Create collection → Function in development')
    input('🔙 Press Enter to return...')


def _update_collection_placeholder() -> None:
    cid = input_int("Enter collection ID to update (or 'q' to cancel): ")
    if cid is None:
        print('Update collection cancelled.')
    else:
        print(f'🔧 Update collection {cid} → Function in development')
    input('🔙 Press Enter to return...')


def _delete_collection(manager: MetabaseAPIManager) -> None:
    cid = input_int("Enter collection ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete collection cancelled.')
        input('🔙 Press Enter to return...')
        return
    confirm_and_delete('collection', cid, manager.collection.delete_specific_collection)


def _view_collection_items(manager: MetabaseAPIManager, cid: int) -> None:
    try:
        col = manager.collection.get_specific_collection(cid)
        clear_screen()
        print_collection_info(col)
        view_item = input_str(
            'Press y to view items in this collection, any other key to return: ',
            required=False,
            allow_cancel=False,
        )
        if view_item and view_item.lower() == 'y':
            items = manager.collection.get_colletion_detail(collection_id=cid, extra='items')
            print_collection_items(items)
            input('🔙 Press Enter to return...')
    except Exception as e:
        print(f'❌ Error: Could not retrieve collection ID {cid}. ({e})')
        input('🔙 Press Enter to exit...')


def collection_menu(manager: MetabaseAPIManager) -> None:
    run_resource_menu(
        title='Collections',
        list_fn=lambda: _list_collections(manager),
        actions={
            'm': ('View collection details', lambda: _view_collection_details(manager)),
            'c': ('Create new collection', _create_collection_placeholder),
            'u': ('Update collection', _update_collection_placeholder),
            'd': ('Delete collection', lambda: _delete_collection(manager)),
        },
        id_handler=lambda cid: _view_collection_items(manager, cid),
    )
