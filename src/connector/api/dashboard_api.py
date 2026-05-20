"""Metabase Dashboard API client."""

from __future__ import annotations

from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource


class DashboardAPI(BaseResource):
    resource = 'dashboard'

    def list_all_dashboards(self) -> list[dict[str, Any]]:
        return self._get().json()

    def get_dashboard_detail(self, dashboard_id: int, extra: str | None = None) -> dict[str, Any]:
        if extra:
            return self._get(dashboard_id, extra).json()
        return self._get(dashboard_id).json()

    def post_dashboard_action(
        self,
        dashboard_id: int,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(dashboard_id, action, json=payload or {}).json()

    def delete_specific_dashboard(self, dashboard_id: int) -> requests.Response:
        return self._delete(dashboard_id)

    def get_save_denormalized_dashboard_url(self, parent_collection_id: int | None = None) -> str:
        if parent_collection_id is not None:
            return self.url('save', 'collection', parent_collection_id)
        return self.url('save', 'collection')

    @staticmethod
    def get_copy_payload(
        collection_id: int | None = None,
        collection_position: int | None = None,
        description: str = '',
        is_deep_copy: bool = False,
        name: str = '',
    ) -> dict[str, Any]:
        return {
            'collection_id': collection_id,
            'collection_position': collection_position,
            'description': description,
            'is_deep_copy': is_deep_copy,
            'name': name,
        }
