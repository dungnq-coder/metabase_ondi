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

    def get_colletion_detail(self, collection_id: int, extra: str = None):
        """
        General method to get collection-related details.
        Examples of `extra`:
            - 'items'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(collection_id, extra_path=extra)).json()

        self.set_self_url(original_url)
        return response

    def post_collection_action(self,
                               collection_id: int,
                               action: str,
                               payload: dict = None):
        """
        General method to perform POST actions on a collection.
        Examples of `action`:
            - ''
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._post(url=self.get_url(collection_id,
                                               extra_path=action),
                              json_data=payload or {}).json()

        self.set_self_url(original_url)
        return response

    def move_collection_to_trash(self, collection_id: int):
        """
        Move a specific collection to the trash before permanent deletion.

        Args:
            collection_id (int): The ID of the collection to move to trash.

        Returns:
            dict: JSON response from the API.
        """
        payload = self.get_put_to_trash_payload(
            description='Move another collection into trash collection',
            name='put to trash')
        # Use the generic PUT action handler
        response = self.put_collection_action(collection_id=collection_id,
                                              payload=payload)
        return response

    def delete_specific_collection(self, collection_id: int):
        """
        Permanently delete a specific collection.

        A collection must first be moved to trash before it can be deleted.
        This function ensures that sequence automatically.

        Args:
            collection_id (int): The ID of the collection to delete.

        Returns:
            requests.Response: The API response from the DELETE request.
        """
        # Step 1: Move to trash
        move_res = self.move_collection_to_trash(collection_id)
        if not isinstance(move_res,
                          dict) or move_res.get('id') != collection_id:
            print(f'⚠️ Failed to move collection {collection_id} to trash.')
            return move_res

        # Step 2: Permanently delete
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(collection_id))
        self.set_self_url(original_url)

        return response

    def put_collection_action(self,
                              collection_id: int,
                              action: str = None,
                              payload: dict = None):
        """
        General method to perform PUT actions on a collection.
        Examples of `action`:
            - ''
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._put(url=self.get_url(collection_id,
                                              extra_path=action),
                             json_data=payload or {}).json()

        self.set_self_url(original_url)
        return response

    def get_put_to_trash_payload(self,
                                 archived: bool = False,
                                 authority_level: str = 'official',
                                 description: str = '',
                                 name: str = '',
                                 parent_id: int = 1):
        return {
            'archived': archived,
            'authority_level': authority_level,
            'description': description,
            'name': name,
            'parent_id': parent_id
        }
