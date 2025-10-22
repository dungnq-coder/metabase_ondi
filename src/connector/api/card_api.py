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

    def get_card_detail(self, card_id: int, extra: str):
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
