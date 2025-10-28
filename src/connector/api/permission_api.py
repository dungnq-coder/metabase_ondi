import json
from pathlib import Path
from pprint import pprint

from core.base_config import BaseConfig
from src.connector.api.base_api_class import Base


class PermissionsAPI(Base):

    def __init__(self, api_token: str, url: str):
        super().__init__(api_token)
        self._api_url = url

    def get_permissions_detail(self, permissions_id: int = None, extra: str = None, **kwargs):
        """
        General method to get permissions-related details.

        Behavior:
            1. If permissions_id is provided → use param_url and build .../{id}/{extra}
            2. If permissions_id is None → use base URL and append /{extra}
            3. If group_id or member_id is provided → treat as .../{extra}/{id}

        Examples:
            get_permissions_detail(1, 'graph')
                → /permissions/1/graph

            get_permissions_detail(extra='graph')
                → /permissions/graph

            get_permissions_detail(extra='group', group_id=3)
                → /permissions/group/3

        Args:
            permissions_id (int, optional): Permission resource ID. If None, uses base URL.
            extra (str, optional): Additional endpoint (e.g., 'group', 'graph', 'membership').
            **kwargs: Optional keyword arguments (e.g., group_id=..., member_id=...).

        Returns:
            requests.Response: API response object.
        """
        original_url = self.get_self_url()

        # --- Case 1: permission_id exists -> standard /permissions/{id}/{extra}
        if permissions_id is not None:
            self.set_self_url(self.get_param_url())
            target_url = self.get_url(permissions_id, extra_path=extra)

        # --- Case 2 & 3: permission_id None
        else:
            group_id = kwargs.get("group_id")
            member_id = kwargs.get("member_id")

            # Case 3: /permissions/{extra}/{group_id or member_id}
            if group_id is not None or member_id is not None:
                sub_id = group_id or member_id
                # set_self_url để format {id} sau extra
                self.set_self_url(f"{self._api_url.rstrip('/')}/{extra}/{{}}")
                target_url = self.get_url(sub_id)

            # Case 2: chỉ có /permissions/{extra}
            else:
                target_url = self.get_url(extra_path=extra)

        # --- Perform the GET request
        response = self._get(url=target_url)

        # --- Restore original URL
        self.set_self_url(original_url)
        return response



    def post_permissions_action(self,
                             permissions_id: int,
                             action: str,
                             payload: dict = None):
        """
        General method to perform POST actions on a permissions.
        Examples of `action`:
            - 'validate'
        """
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())

        response = self._post(url=self.get_url(permissions_id, extra_path=action),
                              json_data=payload or {})

        self.set_self_url(original_url)
        return response


    def delete_specific_permissions(self, permissions_id: int):
        """Delete specific permissions by ID."""
        original_url = self.get_self_url()
        self.set_self_url(self.get_param_url())
        response = self._delete(url=self.get_url(permissions_id))
        self.set_self_url(original_url)
        return response