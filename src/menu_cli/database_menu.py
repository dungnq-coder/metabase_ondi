"""Interactive menu for Metabase databases."""

from __future__ import annotations

from typing import Any

from src.connector.manager import MetabaseAPIManager
from src.menu_cli._base import confirm_and_delete, run_resource_menu
from src.utils.input_utils import input_int, input_str, input_yes_no
from src.utils.print_databases import (
    print_database_details,
    print_database_summary,
    print_databases_list,
)
from src.utils.screen_contact import clear_screen

DEFAULT_SCHEDULE = {
    'schedule_type': 'daily',
    'schedule_hour': 0,
    'schedule_minute': 0,
    'schedule_day': 'sun',
    'schedule_frame': 'first',
}


def _list_databases(manager: MetabaseAPIManager) -> None:
    databases = manager.database.list_all_databases()
    clear_screen()
    print_databases_list(databases)


def _view_database(manager: MetabaseAPIManager, cid: int) -> None:
    database = manager.database.get_database_detail(cid).json()
    clear_screen()
    print_database_details(database)
    input('🔙 Press Enter to return...')


def _prompt_schedule(name: str) -> dict[str, Any]:
    print(f'\n🕒 Enter {name} schedule configuration:')
    print('   Default values:')
    for k, v in DEFAULT_SCHEDULE.items():
        print(f'     - {k}: {v}')

    if input_yes_no('Use default schedule?'):
        print(f'✅ Using default schedule for {name}.')
        return dict(DEFAULT_SCHEDULE)

    return {
        'schedule_type': input_str(
            '  schedule_type (hourly, daily, weekly, monthly): ', required=True
        )
        or DEFAULT_SCHEDULE['schedule_type'],
        'schedule_hour': input_int('  schedule_hour (0-23): ', allow_empty=True) or 0,
        'schedule_minute': input_int('  schedule_minute (0-59): ', allow_empty=True) or 0,
        'schedule_day': input_str('  schedule_day (sun-sat): ', required=True)
        or DEFAULT_SCHEDULE['schedule_day'],
        'schedule_frame': input_str('  schedule_frame (first, mid, last): ', required=True)
        or DEFAULT_SCHEDULE['schedule_frame'],
    }


def _create_database(manager: MetabaseAPIManager) -> None:
    clear_screen()
    print('🆕 Create a new database connection')

    name = input_str('Enter database name: ', required=True)
    engine = input_str(
        'Enter database engine (e.g., bigquery-cloud-sdk, postgres, mysql): ',
        required=True,
    )
    if name is None or engine is None:
        print('Cancelled.')
        input('🔙 Press Enter to return...')
        return

    if engine != 'bigquery-cloud-sdk':
        print(f'⚠️  Engine "{engine}" is not supported yet.')
        input('🔙 Press Enter to return...')
        return

    project_id = input_str('Enter BigQuery project_id: ', required=True)
    if project_id is None:
        print('Cancelled.')
        input('🔙 Press Enter to return...')
        return
    dataset_id = input_str(
        'Enter BigQuery dataset_id (comma separated) or q to skip: ',
        required=False,
    )
    details = manager.database.create_bigquery_details(project_id=project_id, dataset_id=dataset_id)

    is_full_sync = input_yes_no('Enable full schema sync? ') or False
    auto_run_queries = input_yes_no('Enable auto run queries?') or False
    is_on_demand = input_yes_no('Is on-demand connection?') or False
    connection_source = (
        input_str("Connection source ('admin'/'setup', default admin): ", required=False) or 'admin'
    )

    payload = manager.database.build_database_payload(
        name=name,
        engine=engine,
        details=details,
        is_full_sync=is_full_sync,
        auto_run_queries=auto_run_queries,
        is_on_demand=is_on_demand,
        connection_source=connection_source,
        cache_schedule=_prompt_schedule('cache_field_values'),
        metadata_schedule=_prompt_schedule('metadata_sync'),
    )

    print('\nSending create database request...')
    response = manager.database.create_database(payload)
    if response.status_code < 400:
        print(f"✅ Database '{name}' created successfully!")
        print_database_summary(db=response.json())
    else:
        print(f'❌ Failed to create database. Status: {response.status_code}')
        print(f'Response: {response.text}')

    input('🔙 Press Enter to return...')


def _update_schedule(name: str, current: dict[str, Any]) -> dict[str, Any]:
    print(f'\nUpdate schedule for {name}:')
    return {
        'schedule_type': input(
            f'  schedule_type (current: {current.get("schedule_type")}): '
        ).strip()
        or current.get('schedule_type'),
        'schedule_hour': input_int(
            f'  schedule_hour (current: {current.get("schedule_hour")}): ', allow_empty=True
        )
        or current.get('schedule_hour'),
        'schedule_minute': input_int(
            f'  schedule_minute (current: {current.get("schedule_minute")}): ', allow_empty=True
        )
        or current.get('schedule_minute'),
        'schedule_day': input(f'  schedule_day (current: {current.get("schedule_day")}): ').strip()
        or current.get('schedule_day'),
        'schedule_frame': input(
            f'  schedule_frame (current: {current.get("schedule_frame")}): '
        ).strip()
        or current.get('schedule_frame'),
    }


def _update_database(manager: MetabaseAPIManager) -> None:
    cid = input_int("Enter database ID to update (or 'q' to cancel): ")
    if cid is None:
        print('Update cancelled.')
        input('🔙 Press Enter to return...')
        return

    db_info = manager.database.get_database_detail(cid).json()
    print('\n📝 Leave blank to keep current value.\n')

    name = input(f'Database name (current: {db_info.get("name")}): ').strip() or db_info.get('name')
    is_full_sync = input_yes_no(
        f'Enable full schema sync? (current: {db_info.get("is_full_sync")})'
    )
    auto_run_queries = input_yes_no(
        f'Enable auto run queries? (current: {db_info.get("auto_run_queries")})'
    )
    is_on_demand = input_yes_no(
        f'Is on-demand connection? (current: {db_info.get("is_on_demand")})'
    )

    schedules = db_info.get('schedules', {})
    metadata_schedule = _update_schedule('metadata_sync', schedules.get('metadata_sync', {}))
    cache_schedule = _update_schedule('cache_field_values', schedules.get('cache_field_values', {}))

    details = db_info.get('details', {})
    if db_info.get('engine') == 'bigquery-cloud-sdk':
        print('\nUpdate BigQuery details:')
        project_id = input(
            f'  project-id (current: {details.get("project-id")}): '
        ).strip() or details.get('project-id')
        dataset_id = input(
            f'  dataset-filters-patterns (current: {details.get("dataset-filters-patterns")}): '
        ).strip() or details.get('dataset-filters-patterns')
        details = manager.database.create_bigquery_details(project_id, dataset_id)

    payload = {
        'name': name,
        'engine': db_info.get('engine'),
        'is_full_sync': is_full_sync,
        'auto_run_queries': auto_run_queries,
        'is_on_demand': is_on_demand,
        'schedules': {'metadata_sync': metadata_schedule, 'cache_field_values': cache_schedule},
        'details': details,
        'cache_ttl': db_info.get('cache_ttl'),
        'refingerprint': db_info.get('refingerprint'),
        'is_sample': db_info.get('is_sample'),
    }

    response = manager.database.update_specific_database(cid, payload)
    sync_res = manager.database.post_database_action(database_id=cid, action='sync_schema')

    if response.status_code < 400 and sync_res.status_code < 400:
        print(f"✅ Database '{name}' updated successfully!")
    else:
        print(
            '❌ Failed to update database. '
            f'Update status: {response.status_code}, sync status: {sync_res.status_code}'
        )

    input('🔙 Press Enter to return...')


def _delete_database(manager: MetabaseAPIManager) -> None:
    did = input_int("Enter database ID to delete (or 'q' to cancel): ")
    if did is None:
        print('Delete cancelled.')
        input('🔙 Press Enter to return...')
        return
    confirm_and_delete('database', did, manager.database.delete_specific_database)


def database_menu(manager: MetabaseAPIManager) -> None:
    run_resource_menu(
        title='Databases',
        list_fn=lambda: _list_databases(manager),
        actions={
            'c': ('Create new database', lambda: _create_database(manager)),
            'u': ('Update database', lambda: _update_database(manager)),
            'd': ('Delete database', lambda: _delete_database(manager)),
        },
        id_handler=lambda cid: _view_database(manager, cid),
    )
