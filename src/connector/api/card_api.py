"""Metabase Card API client."""

from __future__ import annotations

import copy
from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource


class CardAPI(BaseResource):
    resource = 'card'

    def list_all_cards(self) -> list[dict[str, Any]]:
        return self._get().json()

    def get_list_dashboard_with_specific_card(self, card_id: int) -> Any:
        return self._get(card_id, 'dashboards').json()

    def get_card_detail(self, card_id: int, extra: str | None = None) -> dict[str, Any]:
        return self._get(card_id, extra).json() if extra else self._get(card_id).json()

    def post_card_action(
        self, card_id: int, action: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._post(card_id, action, json=payload or {}).json()

    def delete_specific_card(self, card_id: int) -> requests.Response:
        return self._delete(card_id)

    def update_specific_card(self, card_id: int, payload: dict[str, Any]) -> requests.Response:
        return self._put(card_id, json=payload or {})

    def get_update_payload(
        self,
        original_payload: dict[str, Any],
        database_id: int,
        table_id: int | None = None,
        mapping: dict[int, int] | None = None,
    ) -> dict[str, Any]:
        """Update Metabase card payload to use a new database/table and remap field IDs."""
        updated = copy.deepcopy(original_payload)
        dataset_query = updated.get('dataset_query', {})
        query_obj = dataset_query.get('query', {})

        updated['database_id'] = database_id
        dataset_query['database'] = database_id

        if table_id is not None:
            updated['table_id'] = table_id
            query_obj['source-table'] = table_id

        if mapping:

            def remap_field_ref(obj: Any) -> None:
                if isinstance(obj, list):
                    if len(obj) >= 2 and obj[0] == 'field' and isinstance(obj[1], int):
                        old_id = obj[1]
                        new_id = mapping.get(old_id)
                        if new_id:
                            obj[1] = new_id
                            if table_id and len(obj) > 2 and isinstance(obj[2], dict):
                                obj[2]['base-type'] = obj[2].get('base-type', 'type/Integer')
                    for item in obj:
                        remap_field_ref(item)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        remap_field_ref(v)

            remap_field_ref(query_obj)

            for col in updated.get('result_metadata') or []:
                old_id = col.get('id')
                new_id = mapping.get(old_id)
                if new_id:
                    col['id'] = new_id
                if table_id is not None:
                    col['table_id'] = table_id

        dataset_query['query'] = query_obj
        updated['dataset_query'] = dataset_query
        return updated
