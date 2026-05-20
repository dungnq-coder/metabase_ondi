"""Metabase Timeline API client."""

from __future__ import annotations

from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource


class TimelineAPI(BaseResource):
    resource = 'timeline'

    def list_all_timelines(self) -> requests.Response:
        return self._get()

    def list_all_timeline_with_events(self) -> requests.Response:
        return self._get(params={'include': 'events'})

    def get_list_timeline_with_specific_collection(self, collection_id: int) -> requests.Response:
        return self._get('collection', collection_id)

    def get_timeline_detail(self, timeline_id: int, extra: str | None = None) -> requests.Response:
        if extra:
            return self._get(timeline_id, extra)
        return self._get(timeline_id)

    def post_timeline_action(self, payload: dict[str, Any] | None = None) -> requests.Response:
        return self._post(json=payload or {})

    def delete_specific_timeline(self, timeline_id: int) -> requests.Response:
        return self._delete(timeline_id)

    def update_specific_timeline(
        self, timeline_id: int, payload: dict[str, Any]
    ) -> requests.Response:
        return self._put(timeline_id, json=payload or {})

    @staticmethod
    def get_update_timeline_payload(
        archived: bool = False,
        collection_id: int = 1,
        default: bool = False,
        description: str = '',
        icon: str = 'star',
        name: str = '',
    ) -> dict[str, Any]:
        return {
            'archived': archived,
            'collection_id': collection_id,
            'default': default,
            'description': description,
            'icon': icon,
            'name': name,
        }
