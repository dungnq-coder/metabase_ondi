from src.connector.api.base_api_class import Base


class CollectionAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_root_url(self) -> str:
        """
        Needs init url not other endpoint like items...
        """
        return f'{self._api_url}/root'

    def get_trash_url(self) -> str:
        """
        Needs init url not other endpoint like items...
        """
        return f'{self._api_url}/trash'

    def get_collection_items_url(self, collection_id: int) -> str:
        return f'{self._api_url}{collection_id}/items'

    def get_self_url(self) -> str:
        return self._api_url

    def set_self_url(self, url: str) -> None:
        self._api_url = url
