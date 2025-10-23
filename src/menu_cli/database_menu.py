import json
from pathlib import Path
from pprint import pprint

from src.connector.manager import MetabaseAPIManager
from src.utils.input_utils import (get_multiline_input, input_int, input_str,
                                   input_yes_no)
from src.utils.process_response_data import *
from src.utils.screen_contact import clear_screen


def list_databases(manager: MetabaseAPIManager):
    databases = manager.database.list_all_databases()
    clear_screen()
    print_databases_list(databases)


def view_database(manager: MetabaseAPIManager, cid: int):
    database = manager.database.get_database_detail(cid)
    clear_screen()
    print_database_details(database)
    input('🔙 Press Enter to return...')


def create_database(manager: MetabaseAPIManager):
    clear_screen()
    print("🆕 Create a new database connection")

    name = input_str("Enter database name: ", required=True)
    engine = input_str("Enter database engine (e.g., bigquery-cloud-sdk, postgres, mysql): ", required=True)

    details = {}
    if engine == "bigquery-cloud-sdk":
        project_id = input_str("Enter BigQuery project_id: ", required=True)
        dataset_id = input_str("Enter BigQuery dataset_id: ", required=True)
        details = manager.database.create_bigquery_details(project_id=project_id, dataset_id=dataset_id)
    else:
        print(f"{engine} will support soon.")
    
    is_full_sync = input_yes_no("Enable full schema sync? ")
    auto_run_queries = input_yes_no("Enable auto run queries?")
    is_on_demand = input_yes_no("Is on-demand connection?")
    cache_ttl = input_int("Cache TTL (minutes), or leave blank for default (1): ", allow_empty=True)
    if cache_ttl is None:
        cache_ttl = 1
    connection_source = input_str("Connection source ('admin' or 'setup'), or leave blank for default (admin): ", required=True)

    def input_schedule(name):
        print(f"\nEnter {name} schedule:")
        schedule_type = input_str("  schedule_type (hourly, daily, weekly, monthly): ", required=True)
        schedule_hour = input_int("  schedule_hour (0-23): ")
        schedule_minute = input_int("  schedule_minute (0-59): ")
        schedule_day = input_str("  schedule_day (sun, mon, tue, wed, thu, fri, sat): ")
        schedule_frame = input_str("  schedule_frame (first, mid, last): ")
        return {
            "schedule_type": schedule_type,
            "schedule_hour": schedule_hour,
            "schedule_minute": schedule_minute,
            "schedule_day": schedule_day,
            "schedule_frame": schedule_frame,
        }
    
    cache_schedule = input_schedule("cache_field_values")
    metadata_schedule = input_schedule("metadata_sync")

    payload = manager.database.build_database_payload(
        name=name,
        engine=engine,
        details=details,
        is_full_sync=is_full_sync,
        auto_run_queries=auto_run_queries,
        is_on_demand=is_on_demand,
        cache_ttl=cache_ttl,
        connection_source=connection_source,
        cache_schedule=cache_schedule,
        metadata_schedule=metadata_schedule
    )

    Path("debug").mkdir(exist_ok=True)
    with open("debug/payload_preview.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    print("\nSending create database request...")
    response = manager.database._post(
        url=manager.database.get_self_url(),
        json_data=payload,
    )

    if response.status_code < 400:
        print(f"✅ Database '{name}' created successfully!")
    else:
        print(f"❌ Failed to create database. Status: {response.status_code}")
        print(f"Response: {response.text}")

    input('🔙 Press Enter to return...')


def update_database(manager: MetabaseAPIManager):
    cid = input_int("Enter database ID to update (or 'q' to cancel): ")
    if cid is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return
    response = None
    if response.status_code < 400:
        print(f'database ID {cid} updated successfully.')
    input('🔙 Press Enter to return...')


def delete_database(manager: MetabaseAPIManager):
    cid = input_int("Enter database ID to delete (or 'q' to cancel): ")
    if cid is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return

    confirm = input_yes_no(f'Are you sure you want to delete database ID {cid}?')
    if confirm:
        pass
    else:
        print('Delete cancelled.')

    input('🔙 Press Enter to return...')


def database_menu(manager: MetabaseAPIManager):
    while True:
        list_databases(manager)

        print('\nOptions:')
        print('  [id] - View database by ID')
        print('  c    - Create new database connect')
        print('  u    - Update database')
        print('  d    - Delete database')
        print('  b    - Back to main menu')

        action = input_str('\n🔢 Choose (ID / action): ',
                           required=True,
                           allow_cancel=False).strip()

        if action.lower() == 'b':
            break
        elif action.lower() == 'c':
            create_database(manager)
        elif action.lower() == 'u':
            update_database(manager)
        elif action.lower() == 'd':
            delete_database(manager)
        elif action.isdigit():
            view_database(manager, int(action))
        else:
            input('❗ Invalid choice. Press Enter to continue.')
