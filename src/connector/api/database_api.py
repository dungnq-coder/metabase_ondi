import json
from pathlib import Path

from core.base_config import BaseConfig
from src.connector.api.base_api_class import Base


class DatabaseAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def list_all_databases(self):
        """List all databases."""
        return self._get(self.get_self_url()).json()

    def get_database_detail(self, database_id: int, extra: str = None):
        """
        General method to get database-related details.
        Examples of `extra`:
            - 'autocomplete_suggestions'
            - 'card_autocomplete_suggestions'
            - 'fields'
            - 'healthcheck'
            - 'metadata'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(database_id, extra_path=extra)).json()

        self.set_self_url(original_url)
        return response

    def post_database_action(self,
                             database_id: int,
                             action: str,
                             payload: dict = None):
        """
        General method to perform POST actions on a database.
        Examples of `action`:
            - 'validate'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._post(url=self.get_url(database_id, extra_path=action),
                              json_data=payload or {})

        self.set_self_url(original_url)
        return response

    def build_database_payload(
        self,
        name: str,
        engine: str,
        details: dict,
        *,
        is_full_sync: bool = True,
        auto_run_queries: bool = True,
        is_on_demand: bool = False,
        cache_ttl: int | None = 1,
        connection_source: str = 'admin',
        cache_schedule: dict | None = None,
        metadata_schedule: dict | None = None,
    ):
        """
        Create a complete payload for POST /api/database in Metabase.

        Args:
            name (str): Name of the database.
            engine (str): Type of engine ('bigquery-cloud-sdk', 'postgres', 'mysql', etc.).
            details (dict): Specific connection information.
            is_full_sync (bool): Whether to periodically sync the entire schema.
            auto_run_queries (bool): Whether to automatically run query previews in Metabase.
            is_on_demand (bool): For databases that connect only on demand.
            cache_ttl (int | None): Cache TTL for field values (in minutes), None for default.
            connection_source (str): Either 'admin' or 'setup'.
            cache_schedule (dict | None): Schedule for refreshing cache field values.
            metadata_schedule (dict | None): Schedule for metadata synchronization.
        """

        def validate_schedule(sch: dict | None, default_type='daily'):
            """
            Chuẩn hóa schedule theo Metabase format.
            """
            if not sch:
                return {
                    'schedule_type': default_type,
                    'schedule_hour': 0,
                    'schedule_minute': 0,
                    'schedule_day': 'sun',
                    'schedule_frame': 'first'
                }

            return {
                'schedule_type': sch.get('schedule_type', default_type),
                'schedule_hour': sch.get('schedule_hour', 0),
                'schedule_minute': sch.get('schedule_minute', 0),
                'schedule_day': sch.get('schedule_day', 'sun'),
                'schedule_frame': sch.get('schedule_frame', 'first'),
            }

        payload = {
            'name': name,
            'engine': engine,
            'details': details,
            'is_full_sync': is_full_sync,
            'auto_run_queries': auto_run_queries,
            'is_on_demand': is_on_demand,
            'refingerprint': False,
            # "cache_ttl": cache_ttl,
            'connection_source': connection_source,
            'schedules': {
                'cache_field_values':
                validate_schedule(cache_schedule, 'daily'),
                'metadata_sync': validate_schedule(metadata_schedule,
                                                   'hourly'),
            },
        }

        return payload

    def create_bigquery_details(self, project_id: str) -> dict:
        """
        Create 'details' part for BigQuery database payload.
        """
        config = BaseConfig()
        service_account_path = Path(config.service_account)

        if not service_account_path.exists():
            raise FileNotFoundError(
                f'❌ Service account file not found: {service_account_path}')

        with open(service_account_path, 'r', encoding='utf-8') as f:
            sa_json = f.read()

        return {
            'project-id': project_id,
            'service-account-json': sa_json,
        }

    def create_schedule(self,
                        schedule_type: str = 'daily',
                        schedule_hour: int = 0,
                        schedule_minute: int = 0,
                        schedule_day: str = 'sun',
                        schedule_frame: str = 'first') -> dict:
        """
        Create a schedule dictionary for cache_field_values or metadata_sync.

        Args:
            schedule_type (str): The frequency of the schedule.
                Options include "hourly", "daily", "weekly", "monthly".
            schedule_hour (int): The hour of the day the schedule runs (0-23).
            schedule_minute (int): The minute of the hour the schedule runs (0-59).
            schedule_day (str): The day of the week the schedule runs.
                Options: "sun", "mon", "tue", "wed", "thu", "fri", "sat".
            schedule_frame (str): The frame within the schedule day.
                Options: "first", "mid", "last".

        Returns:
            dict: A dictionary representing the schedule configuration.
        """
        return {
            'schedule_type': schedule_type,
            'schedule_hour': schedule_hour,
            'schedule_minute': schedule_minute,
            'schedule_day': schedule_day,
            'schedule_frame': schedule_frame,
        }

    def delete_specific_database(self, database_id: int):
        """Delete specific database by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(database_id))
        self.set_self_url(original_url)
        return response
