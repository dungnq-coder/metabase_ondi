from src.connector.api.base_api_class import Base


class CardAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_card_items_url(self, card_id: int) -> str:
        return f'{self._api_url}/{card_id}/items'

    def get_card_query_metadata_url(self, card_id: int) -> str:
        return f'{self._api_url}/{card_id}/query_metadata'

    def get_card_query_url(self, card_id: int) -> str:
        return f'{self._api_url}/{card_id}/query'

    def get_card_public_link_url(self, card_id: int) -> str:
        return f'{self._api_url}/{card_id}/public_link'

    def get_card_copy_url(self, card_id: int) -> str:
        return f'{self._api_url}/{card_id}/copy'
