from src.connector.api.base_api_class import Base


class CardAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def list_all_cards(self):
        """List all cards."""
        return self._get(self.get_self_url()).json()

    def get_list_dashboard_with_specific_card(self, card_id: int):
        """Get list of dashboards containing a specific card."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(card_id, extra_path='dashboards')).json()

        self.set_self_url(original_url)
        return response

    def get_card_detail(self, card_id: int, extra: str = None):
        """
        General method to get card-related details.
        Examples of `extra`:
            - 'items'
            - 'query'
            - 'query_metadata'
            - 'public_link'
            - 'dashboards'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(card_id, extra_path=extra)).json()

        self.set_self_url(original_url)
        return response

    def post_card_action(self,
                         card_id: int,
                         action: str,
                         payload: dict = None):
        """
        General method to perform POST actions on a card.
        Examples of `action`:
            - 'copy'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._post(url=self.get_url(card_id, extra_path=action),
                              json_data=payload or {}).json()

        self.set_self_url(original_url)
        return response

    def delete_specific_card(self, card_id: int):
        """Delete specific card by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(card_id))
        self.set_self_url(original_url)
        return response

    def get_update_payload(self, original_payload: dict, database_id: int,
                           query: str) -> dict:
        """
        Update the database_id and SQL query in the original Metabase card payload.

        Args:
            original_payload (dict): The current card payload data.
            database_id (int): The new database ID to be applied.
            query (str): The new SQL query string.

        Returns:
            dict: The updated payload with the new database ID and query.
        """

        # Tạo bản sao để không làm thay đổi bản gốc
        updated = original_payload.copy()

        # Cập nhật các giá trị chính
        updated['database_id'] = database_id
        updated['dataset_query']['database'] = database_id
        updated['dataset_query']['native']['query'] = query

        return updated

    def update_specific_card(self, card_id: int, payload: dict):
        """Update specific card by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._put(url=self.get_url(card_id),
                             json_data=payload or {}).json()
        self.set_self_url(original_url)
        return response
