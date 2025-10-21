from src.connector.api.base_api_class import Base


class DashboardAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_link_save_denormalized_dashboard_url(
            self, parent_collection_id: int = None) -> str:
        return f'{self._api_url}/save/collection/{parent_collection_id}' if parent_collection_id else f'{self._api_url}/save/collection/'

    def get_dashboard_items_url(self, dashboard_id: int) -> str:
        return f'{self._api_url}/{dashboard_id}/items'

    def get_dashboard_query_metadata_url(self, dashboard_id: int) -> str:
        return f'{self._api_url}/{dashboard_id}/query_metadata'

    def get_dashboard_related_url(self, dashboard_id: int) -> str:
        return f'{self._api_url}/{dashboard_id}/related'

    def get_dashboard_public_link_url(self, dashboard_id: int) -> str:
        return f'{self._api_url}/{dashboard_id}/public_link'

    def get_dashboard_copy_url(self, dashboard_id: int) -> str:
        return f'{self._api_url}/{dashboard_id}/copy'
