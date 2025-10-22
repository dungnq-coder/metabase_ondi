from src.connector.api.base_api_class import Base


class CollectionAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_root_url(self) -> str:
        """
        Needs init url not other endpoint like items...
        """
        url = self._api_url.rstrip('/')
        return f'{url}/root'

    def get_trash_url(self) -> str:
        """
        Needs init url not other endpoint like items...
        """
        url = self._api_url.rstrip('/')
        return f'{url}/trash'

    def get_tree_url(self) -> str:
        """
        Needs init url not other endpoint like items...
        """
        url = self._api_url.rstrip('/')
        return f'{url}/tree'

    def list__all_collections(self):
        """List all collections."""
        return self._get(self.get_self_url()).json()

    def list_all_collections_in_tree(self):
        """List all collections."""
        return self._get(self.get_tree_url()).json()

    def get_specific_collection(self, collection_id: int):
        """Get specific collection by ID."""
        url = self.get_self_url()
        url_new = self.get_param_url()
        self.set_self_url(url_new)

        response = self._get(url=self.get_url(collection_id)).json()
        self.set_self_url(url)

        return response

    def get_items_in_a_specific_collection(self, collection_id: int):
        """Get specific collection by ID."""
        url = self.get_self_url()
        url_new = self.get_param_url()
        self.set_self_url(url_new)

        response = self._get(
            url=self.get_url(collection_id, extra_path='items')).json()
        self.set_self_url(url)

        return response
