import copy

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

        if extra:
            response = self._get(
                url=self.get_url(card_id, extra_path=extra)).json()
        else:
            response = self._get(url=self.get_url(card_id)).json()

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

    def get_update_payload(
            self,
            original_payload: dict,
            database_id: int,
            table_id: int = None,
            mapping: dict = None  # mapping: old_field_id -> new_field_id
    ) -> dict:
        """
        Update Metabase card payload to use a new database/table and remap field IDs.
        """
        updated = copy.deepcopy(original_payload)
        dataset_query = updated.get('dataset_query', {})
        query_obj = dataset_query.get('query', {})

        # --- Always update database_id ---
        updated['database_id'] = database_id
        dataset_query['database'] = database_id

        # --- Update table_id ---
        old_table_id = query_obj.get('source-table')
        if table_id is not None:
            updated['table_id'] = table_id
            query_obj['source-table'] = table_id

        # --- Remap field IDs in query ---
        if mapping:

            def remap_field_ref(obj):
                if isinstance(obj, list):
                    # Cấu trúc ["field", <id>, {...}]
                    if len(obj) >= 2 and obj[0] == 'field' and isinstance(
                            obj[1], int):
                        old_id = obj[1]
                        new_id = mapping.get(old_id)
                        if new_id:
                            obj[1] = new_id
                            # Cập nhật base-type nếu cần
                            if table_id and len(obj) > 2 and isinstance(
                                    obj[2], dict):
                                obj[2]['base-type'] = obj[2].get(
                                    'base-type', 'type/Integer')
                    # Đệ quy cho từng phần tử
                    for i in range(len(obj)):
                        remap_field_ref(obj[i])
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        remap_field_ref(v)

            remap_field_ref(query_obj)

            # --- Update result_metadata ---
            for col in updated.get('result_metadata') or []:
                old_id = col.get('id')
                new_id = mapping.get(old_id)
                if new_id:
                    col['id'] = new_id
                if table_id is not None:
                    col['table_id'] = table_id

        updated['dataset_query']['query'] = query_obj
        updated['dataset_query'] = dataset_query

        return updated

    def update_specific_card(self, card_id: int, payload: dict):
        """Update specific card by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._put(url=self.get_url(card_id),
                             json_data=payload or {})
        self.set_self_url(original_url)
        return response
