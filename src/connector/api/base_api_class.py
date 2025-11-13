import requests


class Base:

    def __init__(self, api_token: str, auth_type: str = 'api_key'):
        self._api_token = api_token
        self._api_url = ''
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
        print(response.text)
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

    def get_url(self, *args, **kwargs) -> str:
        """
        Build URL by formatting self._api_url with positional arguments.
        Extra path segments (if any) can be passed as kwargs['extra_path'] (optional).
        """
        try:
            base_url = self._api_url.format(*args)
        except IndexError:
            raise ValueError(
                'Not enough arguments provided to format the URL.')

        extra_path = kwargs.get('extra_path')
        if extra_path:
            if isinstance(extra_path, (list, tuple)):
                extra = '/'.join(str(p).strip('/') for p in extra_path)
            else:
                extra = str(extra_path).strip('/')
            return f"{base_url.rstrip('/')}/{extra}"
        return base_url

    def get_param_url(self) -> str:
        url = self._api_url.rstrip('/')
        return url + '/{}'

    def get_self_url(self) -> str:
        return self._api_url

    def set_self_url(self, url: str) -> None:
        self._api_url = url
