from pprint import pprint

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.process_response_data import *
from src.utils.screen_contact import clear_screen


def list_cards(manager: MetabaseAPIManager):
    cards = manager.card.list_all_cards()
    clear_screen()
    print('📄 All Cards')
    print('=' * 60)
    for c in cards:
        print(f"[{c['id']}] {c['name']}")


def view_card(manager: MetabaseAPIManager, cid: int):
    card = manager.card.get_card_detail(cid)
    clear_screen()
    print_card_details(card)
    input('🔙 Press Enter to return...')


def create_card(manager: MetabaseAPIManager):
    print('🔧 Create card → Function in development')
    input('🔙 Press Enter to return...')


def update_card(manager: MetabaseAPIManager):
    cid = input_int("Enter card ID to update (or 'q' to cancel): ")
    if cid is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    card_detail = manager.card.get_card_detail(cid)
    database_id = input_int("Enter new database ID (or 'q' to cancel): ")
    if database_id is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    query = get_multiline_input("Enter new SQL query (or 'q' to cancel): ")
    if query is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    updated_payload = manager.card.get_update_payload(card_detail, database_id,
                                                      query)
    response = manager.card.update_specific_card(cid, updated_payload)
    print_card_details(response)

    # if response.status_code < 400:
    #     print(f'Card ID {cid} updated successfully.')
    input('🔙 Press Enter to return...')


def delete_card(manager: MetabaseAPIManager):
    cid = input_int("Enter card ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(f'Are you sure you want to delete card ID {cid}?')
    if confirm:
        # Giả sử manager.card.delete_specific_card(cid) trả về response
        res = manager.card.delete_specific_card(cid)
        if res.status_code < 400:
            print(f'Card ID {cid} deleted successfully.')
        else:
            print(
                f'Failed to delete card ID {cid}. Status code: {res.status_code}'
            )
    else:
        print('Delete cancelled.')

    input('🔙 Press Enter to return...')


def card_menu(manager: MetabaseAPIManager):
    while True:
        list_cards(manager)

        print('\nOptions:')
        print('  [id] - View card by ID')
        print('  c    - Create new card')
        print('  u    - Update card')
        print('  d    - Delete card')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'c':
            create_card(manager)
        elif action.lower() == 'u':
            update_card(manager)
        elif action.lower() == 'd':
            delete_card(manager)
        elif action.isdigit():
            view_card(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
