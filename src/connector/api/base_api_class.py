import requests


class Base:

    def __init__(self, api_token: str, auth_type: str = 'api_key'):
        self._api_token = api_token
        if auth_type == 'api_key':
            self._headers = {'x-api-key': api_token}
        elif auth_type == 'session':
            self._headers = {'X-Metabase-Session': api_token}
        else:
            raise ValueError("auth_type must be 'api_key' or 'session'")

    def _request(self,
                 method: str,
                 url: str,
                 *,
                 params: dict = None,
                 json_data: dict = None):
        response = requests.request(method=method,
                                    url=url,
                                    headers=self._headers,
                                    params=params,
                                    json=json_data)
        response.raise_for_status()
        return response

    def _get(self, url: str, params: dict = None):
        return self._request('GET', url, params=params)

    def _post(self, url: str, json_data: dict = None, params: dict = None):
        return self._request('POST', url, json_data=json_data, params=params)

    def _put(self, url: str, json_data: dict = None, params: dict = None):
        return self._request('PUT', url, json_data=json_data, params=params)

    def _delete(self, url: str, params: dict = None):
        return self._request('DELETE', url, params=params)

    def get_url(self, **kwargs) -> str:
        missing_params = [
            param for param in self.PARAMS if param not in kwargs
        ]
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}")

        return self.api_url.format(*[kwargs[param] for param in self.PARAMS])

    def get_self_url(self) -> str:
        return self._api_url

    def set_self_url(self, url: str) -> None:
        self._api_url = url
