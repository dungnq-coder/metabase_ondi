import copy

from src.connector.api.base_api_class import Base


class TimelineAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def list_all_timelines(self):
        """List all timelines."""
        return self._get(self.get_self_url())

    def get_list_timeline_with_specific_collection(self, collection_id: int):
        """Get list of timeline from a specific collection."""
        original_url = self.get_self_url()
        self.set_self_url(f'{original_url}/collection')
        self.set_self_url(self.get_param_url())

        response = self._get(url=self.get_url(collection_id))

        self.set_self_url(original_url)
        return response

    def get_timeline_detail(self, timeline_id: int, extra: str = None):
        """
        General method to get card-related details.
        Examples of `extra`:
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(
            url=self.get_url(timeline_id, extra_path=extra))

        self.set_self_url(original_url)
        return response

    def post_timeline_action(self,
                         payload: dict = None):
        """
        General method to perform POST actions on a card.
        Examples of `action`:
            - 'copy'
        """

        response = self._post(url=self.get_self_url(),
                              json_data=payload or {})
        return response

    def delete_specific_timeline(self, timeline_id: int):
        """Delete specific timeline by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(timeline_id))
        self.set_self_url(original_url)
        return response
    
    def get_update_timeline_payload(self, archived: bool = False, 
                                    collection_id: int = 1, 
                                    default: bool = True, 
                                    description: str = "", 
                                    icon: str = "star", 
                                    name: str = "") -> dict:
        """Generate payload for updating a timeline."""
        payload = {
            "archived": archived,
            "collection_id": collection_id,
            "default": default,
            "description": description,
            "icon": icon,
            "name": name
        }
        return payload

    def update_specific_timeline(self, timeline_id: int, payload: dict):
        """Update specific timeline by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._put(url=self.get_url(timeline_id),
                             json_data=payload or {})
        self.set_self_url(original_url)
        return response
