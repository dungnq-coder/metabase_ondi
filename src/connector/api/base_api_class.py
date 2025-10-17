import requests

class Base:

    api_url: str = None
    PARAMS: list = []

    def __init__(self, api_token: str):
        self._api_token = api_token
        self._headers = {'Authorization': 'Bearer ' + api_token}

    def _request(self, method: str, url: str, *, params: dict = None, json_data: dict = None):
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
        
        return self.api_url.format(
                *[kwargs[param] for param in self.PARAMS])