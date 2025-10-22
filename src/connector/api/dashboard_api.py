from src.connector.api.base_api_class import Base


class DashboardAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def list_all_dashboards(self):
        """List all dashboards."""
        return self._get(self.get_self_url()).json()

    def get_dashboard_detail(self, dashboard_id: int, extra: str = None):
        """
        General method to get dashboard-related details.
        Examples of `extra`:
            - 'items'
            - 'query_metadata'
            - 'related'
            - 'public_link'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(dashboard_id, extra_path=extra)).json()

        self.set_self_url(original_url)
        return response

    def get_copy_payload(self,
                         collection_id: int = None,
                         collection_position: int = None,
                         description: str = '',
                         is_deep_copy: bool = False,
                         name: str = '') -> dict:
        """
        Prepare payload for copying a dashboard.
        """
        payload = {
            'collection_id': collection_id,
            'collection_position': collection_position,
            'description': description,
            'is_deep_copy': is_deep_copy,
            'name': name
        }
        return payload

    def post_dashboard_action(self,
                              dashboard_id: int,
                              action: str,
                              payload: dict = None):
        """
        General method to perform POST actions on a dashboard.
        Examples of `action`:
            - 'copy'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._post(url=self.get_url(dashboard_id,
                                               extra_path=action),
                              json_data=payload or {}).json()

        self.set_self_url(original_url)
        return response

    def get_save_denormalized_dashboard_url(self,
                                            parent_collection_id: int = None
                                            ) -> str:
        """
        Get URL to save denormalized dashboard to a collection.
        """
        suffix = f'{parent_collection_id}' if parent_collection_id else ''
        return f'{self._api_url}/save/collection/{suffix}'

    def delete_specific_dashboard(self, dashboard_id: int):
        """Delete specific dashboard by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(dashboard_id))
        self.set_self_url(original_url)
        return response
