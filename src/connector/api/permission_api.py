"""Metabase Permissions API client."""

from __future__ import annotations

from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource


class PermissionsAPI(BaseResource):
    resource = 'permissions'

    def get_permissions_detail(
        self,
        permissions_id: int | None = None,
        extra: str | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Fetch permissions data.

        Routing:
          - `permissions_id` given → `/permissions/<id>[/<extra>]`
          - `extra` + `group_id|member_id|database_id` → `/permissions/<extra>/<sub_id>`
          - `extra` alone → `/permissions/<extra>`
        """
        if permissions_id is not None:
            if extra:
                return self._get(permissions_id, extra)
            return self._get(permissions_id)

        sub_id = kwargs.get('group_id') or kwargs.get('member_id') or kwargs.get('database_id')
        if sub_id is not None:
            return self._get(extra, sub_id)
        return self._get(extra)

    def post_permissions_action(
        self, action: str, payload: dict[str, Any] | None = None
    ) -> requests.Response:
        return self._post(action, json=payload or {})

    def update_premissions(self, payload: dict[str, Any]) -> requests.Response:
        params = {'skip-graph': 'false', 'force': 'false'}
        return self._put('graph', json=payload or {}, params=params)

    def delete_specific_permissions(self, permissions_id: int) -> requests.Response:
        return self._delete('group', permissions_id)
