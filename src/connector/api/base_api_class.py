"""Base class for Metabase API resource clients."""

from __future__ import annotations

from typing import Any

import requests

from src.http.client import MetabaseClient


class BaseResource:
    """Each subclass binds to a resource path (e.g. 'card', 'dashboard').

    All HTTP calls go through a shared `MetabaseClient` (session, retry, timeout).
    """

    resource: str = ''

    def __init__(self, client: MetabaseClient, resource: str | None = None) -> None:
        self._client = client
        if resource is not None:
            self.resource = resource
        if not self.resource:
            raise ValueError('BaseResource requires a non-empty resource path')

    # ---- URL helpers ----
    def url(self, *segments: Any) -> str:
        return self._client.url(self.resource, *segments)

    # ---- HTTP shortcuts ----
    def _get(self, *segments: Any, params: dict[str, Any] | None = None) -> requests.Response:
        return self._client.get(self.url(*segments), params=params)

    def _post(
        self,
        *segments: Any,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self._client.post(self.url(*segments), json=json, params=params)

    def _put(
        self,
        *segments: Any,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self._client.put(self.url(*segments), json=json, params=params)

    def _delete(self, *segments: Any, params: dict[str, Any] | None = None) -> requests.Response:
        return self._client.delete(self.url(*segments), params=params)
