"""Build and cache Metabase API clients backed by a shared HTTP client."""

from __future__ import annotations

from typing import TypeVar

from src.connector.api.base_api_class import BaseResource
from src.connector.api.card_api import CardAPI
from src.connector.api.collection_api import CollectionAPI
from src.connector.api.dashboard_api import DashboardAPI
from src.connector.api.database_api import DatabaseAPI
from src.connector.api.permission_api import PermissionsAPI
from src.connector.api.timeline_api import TimelineAPI
from src.connector.api.timeline_event_api import TimelineEventAPI
from src.http.client import MetabaseClient

R = TypeVar('R', bound=BaseResource)


class MetabaseAPIManager:
    """Lazy registry of Metabase resource clients. All share one `MetabaseClient`."""

    def __init__(
        self,
        api_token: str,
        base_url: str,
        *,
        client: MetabaseClient | None = None,
    ):
        self._client = client or MetabaseClient(base_url=base_url, api_token=api_token)
        self._cache: dict[type[BaseResource], BaseResource] = {}

    def _get(self, cls: type[R]) -> R:
        if cls not in self._cache:
            self._cache[cls] = cls(self._client)
        return self._cache[cls]  # type: ignore[return-value]

    @property
    def client(self) -> MetabaseClient:
        return self._client

    @property
    def card(self) -> CardAPI:
        return self._get(CardAPI)

    @property
    def collection(self) -> CollectionAPI:
        return self._get(CollectionAPI)

    @property
    def dashboard(self) -> DashboardAPI:
        return self._get(DashboardAPI)

    @property
    def database(self) -> DatabaseAPI:
        return self._get(DatabaseAPI)

    @property
    def permissions(self) -> PermissionsAPI:
        return self._get(PermissionsAPI)

    @property
    def timeline(self) -> TimelineAPI:
        return self._get(TimelineAPI)

    @property
    def timeline_event(self) -> TimelineEventAPI:
        return self._get(TimelineEventAPI)
