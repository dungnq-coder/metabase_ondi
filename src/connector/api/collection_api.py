"""Metabase Collection API client."""

from __future__ import annotations

import logging
from typing import Any

import requests

from src.connector.api.base_api_class import BaseResource

logger = logging.getLogger(__name__)


class CollectionAPI(BaseResource):
    resource = 'collection'

    def list__all_collections(self) -> list[dict[str, Any]]:
        return self._get().json()

    def list_all_collections_in_tree(self) -> list[dict[str, Any]]:
        return self._get('tree').json()

    def get_specific_collection(self, collection_id: int) -> dict[str, Any]:
        return self._get(collection_id).json()

    def get_colletion_detail(self, collection_id: int, extra: str | None = None) -> dict[str, Any]:
        if extra:
            return self._get(collection_id, extra).json()
        return self._get(collection_id).json()

    def post_collection_action(
        self,
        collection_id: int,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._post(collection_id, action, json=payload or {}).json()

    def put_collection_action(
        self,
        collection_id: int,
        action: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if action:
            return self._put(collection_id, action, json=payload or {}).json()
        return self._put(collection_id, json=payload or {}).json()

    def move_collection_to_trash(self, collection_id: int) -> dict[str, Any]:
        payload = self.get_put_to_trash_payload(
            description='Move another collection into trash collection',
            name='put to trash',
        )
        return self.put_collection_action(collection_id=collection_id, payload=payload)

    def delete_specific_collection(self, collection_id: int) -> requests.Response | dict[str, Any]:
        move_res = self.move_collection_to_trash(collection_id)
        if not isinstance(move_res, dict) or move_res.get('id') != collection_id:
            logger.warning('Failed to move collection %s to trash', collection_id)
            return move_res
        return self._delete(collection_id)

    @staticmethod
    def get_put_to_trash_payload(
        archived: bool = False,
        authority_level: str = 'official',
        description: str = '',
        name: str = '',
        parent_id: int = 1,
    ) -> dict[str, Any]:
        return {
            'archived': archived,
            'authority_level': authority_level,
            'description': description,
            'name': name,
            'parent_id': parent_id,
        }
