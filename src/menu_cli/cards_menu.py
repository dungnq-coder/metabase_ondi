from collections import defaultdict
from pprint import pprint

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.mapping import map_field_ids
from src.utils.print_cards import *
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


def update_cards(manager: MetabaseAPIManager):
    """Update database/table cho các Metabase cards với lựa chọn đơn giản hơn."""
    print('=== 🔧 Update Cards Database/Table ===')
    print('1️⃣  Update ALL cards')
    print('2️⃣  Update cards in a specific collection')
    print('3️⃣  Update cards in a specific dashboard')
    print('4️⃣  Update specific card IDs (comma separated)')
    print('0️⃣  Cancel')

    choice = input_int('👉 Choose an option (0-4): ')

    if choice == 0:
        print('❌ Cancelled.')
        return

    cards = manager.card.list_all_cards()
    card_ids = []

    if choice == 1:
        card_ids = [c['id'] for c in cards]
    elif choice == 2:
        collection_id = input_int('Enter collection ID: ')
        card_ids = [
            c['id'] for c in cards
            if c.get('collection', {}).get('id') == collection_id
        ]
    elif choice == 3:
        dashboard_id = input_int('Enter dashboard ID: ')
        card_ids = [
            c['id'] for c in cards if c.get('dashboard_id') == dashboard_id
        ]
    elif choice == 4:
        ids_str = input_str('Enter card IDs separated by comma: ')
        card_ids = [
            int(cid.strip()) for cid in ids_str.split(',')
            if cid.strip().isdigit()
        ]
    else:
        print('❌ Invalid choice.')
        return

    if not card_ids:
        print('⚠️  No cards found. Exiting.')
        return

    print(f'✅ Found {len(card_ids)} card(s) to update.')

    # --- Database & Table ---
    database_id_new = input_int(
        'Enter new database ID (leave blank to keep current): ',
        allow_empty=True)
    table_id_new = input_int(
        'Enter new table ID (leave blank to keep current): ', allow_empty=True)

    cards_to_update = [c for c in cards if c['id'] in card_ids]
    cards_by_db = defaultdict(list)
    for c in cards_to_update:
        db_id_old = c.get('database_id')
        cards_by_db[db_id_old].append(c)

    # --- Update theo nhóm database ---
    for db_id_old, card_objs in cards_by_db.items():
        old_fields = manager.database.get_fields_in_specific_db(db_id_old)

        if database_id_new and database_id_new != db_id_old:
            new_fields = manager.database.get_fields_in_specific_db(
                database_id_new)
            # --- Dùng map_field_ids để tạo mapping old_id -> new_id ---
            field_mapping = map_field_ids(old_fields, new_fields)
        else:
            # Nếu database không đổi, mapping giữ nguyên
            field_mapping = {f['id']: f['id'] for f in old_fields}

        for card_detail in card_objs:
            cid = card_detail['id']
            updated_payload = manager.card.get_update_payload(
                original_payload=card_detail,
                database_id=database_id_new or db_id_old,
                table_id=table_id_new,
                mapping=field_mapping)

            response = manager.card.update_specific_card(cid, updated_payload)
            if response.status_code < 400:
                print(f'✅ Card ID {cid} updated successfully.')
            else:
                print(
                    f'❌ Failed to update Card ID {cid}: {response.status_code} {response.text}'
                )

    input('\n🔙 Press Enter to return to menu...')


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
            update_cards(manager)
        elif action.lower() == 'd':
            delete_card(manager)
        elif action.isdigit():
            view_card(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
