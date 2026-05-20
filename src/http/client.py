"""HTTP client for the Metabase REST API: session, retry, timeout, auth."""

from __future__ import annotations

import logging
from typing import Any, Literal

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

AuthType = Literal['api_key', 'session']
DEFAULT_TIMEOUT = 30.0
RETRY_METHODS = frozenset(['GET', 'HEAD', 'OPTIONS'])  # never retry non-idempotent verbs
RETRY_STATUSES = (429, 500, 502, 503, 504)


class MetabaseClient:
    """Thin wrapper over `requests.Session` for Metabase REST calls.

    - Base URL set once; per-call paths are joined with `/api/<resource>/...`.
    - Retries safe methods on 429/5xx with exponential backoff.
    - Default 30s timeout; override per call.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        auth_type: AuthType = 'api_key',
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._session = requests.Session()

        if auth_type == 'api_key':
            self._session.headers['x-api-key'] = api_token
        elif auth_type == 'session':
            self._session.headers['X-Metabase-Session'] = api_token
        else:
            raise ValueError("auth_type must be 'api_key' or 'session'")

        retry = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=RETRY_STATUSES,
            allowed_methods=RETRY_METHODS,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)

    @property
    def base_url(self) -> str:
        return self._base_url

    def url(self, *path: Any) -> str:
        """Join path segments under the base URL.

        `client.url('card', 5, 'dashboards')` -> `<base>/card/5/dashboards`.
        Absolute URLs are returned unchanged.
        """
        if (
            len(path) == 1
            and isinstance(path[0], str)
            and path[0].startswith(('http://', 'https://'))
        ):
            return path[0]
        joined = '/'.join(str(p).strip('/') for p in path if p is not None and p != '')
        return f'{self._base_url}/{joined}' if joined else self._base_url

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> requests.Response:
        response = self._session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            timeout=timeout if timeout is not None else self._timeout,
        )
        response.raise_for_status()
        return response

    def get(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request('GET', url, params=params)

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request('POST', url, params=params, json=json)

    def put(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        return self.request('PUT', url, params=params, json=json)

    def delete(self, url: str, *, params: dict[str, Any] | None = None) -> requests.Response:
        return self.request('DELETE', url, params=params)
