"""Metabase Timeline Event API client."""

from __future__ import annotations

from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource


class TimelineEventAPI(BaseResource):
    resource = 'timeline-event'

    def get_timeline_event_detail(
        self, timeline_id: int, extra: str | None = None
    ) -> requests.Response:
        if extra:
            return self._get(timeline_id, extra)
        return self._get(timeline_id)

    def post_timeline_event_action(
        self, payload: dict[str, Any] | None = None
    ) -> requests.Response:
        return self._post(json=payload or {})

    def delete_specific_timeline_event(self, timeline_event_id: int) -> requests.Response:
        return self._delete(timeline_event_id)

    def update_specific_timeline(
        self, timeline_id: int, payload: dict[str, Any]
    ) -> requests.Response:
        return self._put(timeline_id, json=payload or {})

    @staticmethod
    def get_create_timeline_event_payload(
        question_id: int | None = None,
        timezone: str = '',
        timestamp: str = '',
        name: str = '',
        archived: bool = False,
        timeline_id: int | None = None,
        source: str = 'collections',
        time_matters: bool = True,
        description: str = '',
        icon: str = 'star',
    ) -> dict[str, Any]:
        return {
            'question_id': question_id,
            'timezone': timezone,
            'timestamp': timestamp,
            'name': name,
            'archived': archived,
            'timeline_id': timeline_id,
            'source': source,
            'time_matters': time_matters,
            'description': description,
            'icon': icon,
        }

    @staticmethod
    def get_update_timeline_event_payload(
        archived: bool = False,
        description: str = '',
        icon: str = 'start',
        name: str = '',
        time_matters: bool = True,
        timeline_id: int | None = None,
        timestamp: str = '',
        timezone: str = '',
    ) -> dict[str, Any]:
        return {
            'archived': archived,
            'description': description,
            'icon': icon,
            'name': name,
            'time_matters': time_matters,
            'timeline_id': timeline_id,
            'timestamp': timestamp,
            'timezone': timezone,
        }
