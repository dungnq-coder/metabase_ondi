"""Metabase Database API client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from src.config.base_config import BaseConfig
from src.connector.api.base_api_class import BaseResource


class DatabaseAPI(BaseResource):
    resource = 'database'

    def list_all_databases(self) -> dict[str, Any]:
        return self._get().json()

    def get_database_detail(self, database_id: int, extra: str | None = None) -> requests.Response:
        params = {
            'include': 'tables',
            'include_editable_data_model': 'true',
            'exclude_uneditable_details': 'true',
        }
        if extra:
            return self._get(database_id, extra, params=params)
        return self._get(database_id, params=params)

    def get_all_table_in_specific_db(self, database_id: int) -> list[dict[str, Any]]:
        schemas = self.get_database_detail(database_id=database_id, extra='schemas').json()
        list_table: list[dict[str, Any]] = []
        for schema in schemas:
            tables = self._get(database_id, 'schema', schema).json()
            if tables:
                for table in tables:
                    list_table.append(
                        {'table_id': table.get('id'), 'table_name': table.get('name')}
                    )
        return list_table

    def get_fields_in_specific_db(self, database_id: int) -> list[dict[str, Any]]:
        return self.get_database_detail(database_id=database_id, extra='fields').json()

    def post_database_action(
        self,
        database_id: int,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self._post(database_id, action, json=payload or {})

    def create_database(self, payload: dict[str, Any]) -> requests.Response:
        return self._post(json=payload)

    def update_specific_database(
        self, database_id: int, payload: dict[str, Any]
    ) -> requests.Response:
        return self._put(database_id, json=payload)

    def delete_specific_database(self, database_id: int) -> requests.Response:
        return self._delete(database_id)

    # ---- Payload builders (pure, no network) ----

    @staticmethod
    def build_database_payload(
        name: str,
        engine: str,
        details: dict[str, Any],
        *,
        is_full_sync: bool = True,
        auto_run_queries: bool = True,
        is_on_demand: bool = False,
        connection_source: str = 'admin',
        cache_schedule: dict[str, Any] | None = None,
        metadata_schedule: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        def validate_schedule(
            sch: dict[str, Any] | None, default_type: str = 'daily'
        ) -> dict[str, Any]:
            base = sch or {}
            return {
                'schedule_type': base.get('schedule_type', default_type),
                'schedule_hour': base.get('schedule_hour', 0),
                'schedule_minute': base.get('schedule_minute', 0),
                'schedule_day': base.get('schedule_day', 'sun'),
                'schedule_frame': base.get('schedule_frame', 'first'),
            }

        return {
            'name': name,
            'engine': engine,
            'details': details,
            'is_full_sync': is_full_sync,
            'auto_run_queries': auto_run_queries,
            'is_on_demand': is_on_demand,
            'refingerprint': False,
            'connection_source': connection_source,
            'schedules': {
                'cache_field_values': validate_schedule(cache_schedule, 'daily'),
                'metadata_sync': validate_schedule(metadata_schedule, 'hourly'),
            },
        }

    @staticmethod
    def create_bigquery_details(project_id: str, dataset_id: str | None = None) -> dict[str, Any]:
        config = BaseConfig()
        service_account_path = Path(config.service_account)
        if not service_account_path.exists():
            raise FileNotFoundError(f'Service account file not found: {service_account_path}')
        sa_json = service_account_path.read_text(encoding='utf-8')
        return {
            k: v
            for k, v in {
                'project-id': project_id,
                'dataset-filters-type': 'inclusion',
                'dataset-filters-patterns': dataset_id,
                'dataset_id': dataset_id,
                'service-account-json': sa_json,
            }.items()
            if v is not None
        }

    @staticmethod
    def create_schedule(
        schedule_type: str = 'daily',
        schedule_hour: int = 0,
        schedule_minute: int = 0,
        schedule_day: str = 'sun',
        schedule_frame: str = 'first',
    ) -> dict[str, Any]:
        return {
            'schedule_type': schedule_type,
            'schedule_hour': schedule_hour,
            'schedule_minute': schedule_minute,
            'schedule_day': schedule_day,
            'schedule_frame': schedule_frame,
        }
