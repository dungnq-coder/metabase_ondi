import copy

from src.connector.api.base_api_class import Base


class TimelineEventAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_timeline_event_detail(self, timeline_id: int, extra: str = None):
        """
        General method to get card-related details.
        Examples of `extra`:
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._get(url=self.get_url(timeline_id, extra_path=extra))

        self.set_self_url(original_url)
        return response

    def post_timeline_event_action(self, payload: dict = None):
        """
        General method to perform POST actions on a timeline event.
        """
        response = self._post(url=self.get_self_url(), json_data=payload or {})
        return response

    def delete_specific_timeline_event(self, timeline_event_id: int):
        """Delete specific timeline event by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(timeline_event_id))
        self.set_self_url(original_url)
        return response

    def get_create_timeline_event_payload(self,
                                          question_id: int = None,
                                          timezone: str = '',
                                          timestamp: str = '',
                                          name: str = '',
                                          archived: bool = False,
                                          timeline_id: int = None,
                                          source: str = 'collections',
                                          time_matters: bool = True,
                                          description: str = '',
                                          icon: str = 'star') -> dict:
        """Generate payload for creating a timeline event."""
        payload = {
            'question_id': question_id,
            'timezone': timezone,
            'timestamp': timestamp,
            'name': name,
            'archived': archived,
            'timeline_id': timeline_id,
            'source': source,
            'time_matters': time_matters,
            'description': description,
            'icon': icon
        }
        return payload

    def get_update_timeline_event_payload(self,
                                          archived: bool = False,
                                          description: str = '',
                                          icon: str = 'start',
                                          name: str = '',
                                          time_matters: bool = True,
                                          timeline_id: int = None,
                                          timestamp: str = '',
                                          timezone: str = '') -> dict:
        """Generate payload for updating a timeline event."""
        payload = {
            'archived': archived,
            'description': description,
            'icon': icon,
            'name': name,
            'time_matters': time_matters,
            'timeline_id': timeline_id,
            'timestamp': timestamp,
            'timezone': timezone
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
