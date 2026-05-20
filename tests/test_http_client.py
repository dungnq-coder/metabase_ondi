import pytest
import requests
import responses

from src.http.client import MetabaseClient


@pytest.fixture
def client() -> MetabaseClient:
    return MetabaseClient(
        base_url='https://example.com/api/',
        api_token='tok',
        max_retries=2,
    )


def test_url_join_strips_slashes(client: MetabaseClient):
    assert client.url('card', 5) == 'https://example.com/api/card/5'
    assert client.url('card', 5, 'dashboards') == 'https://example.com/api/card/5/dashboards'
    assert client.url('/card/', '/5/') == 'https://example.com/api/card/5'


def test_url_passthrough_for_absolute(client: MetabaseClient):
    abs_url = 'https://elsewhere.com/x'
    assert client.url(abs_url) == abs_url


def test_url_empty_returns_base(client: MetabaseClient):
    assert client.url() == 'https://example.com/api'


def test_api_key_header_set():
    c = MetabaseClient('https://x/api', 'mytoken')
    assert c._session.headers['x-api-key'] == 'mytoken'


def test_session_header_set():
    c = MetabaseClient('https://x/api', 'sesstok', auth_type='session')
    assert c._session.headers['X-Metabase-Session'] == 'sesstok'


def test_invalid_auth_type_raises():
    with pytest.raises(ValueError):
        MetabaseClient('https://x/api', 'tok', auth_type='oauth')  # type: ignore[arg-type]


@responses.activate
def test_get_json_round_trip(client: MetabaseClient):
    responses.add(
        responses.GET,
        'https://example.com/api/card/5',
        json={'id': 5, 'name': 'Demo'},
        status=200,
    )
    resp = client.get(client.url('card', 5))
    assert resp.json() == {'id': 5, 'name': 'Demo'}


@responses.activate
def test_retry_on_503(client: MetabaseClient):
    url = 'https://example.com/api/card/1'
    responses.add(responses.GET, url, status=503)
    responses.add(responses.GET, url, status=503)
    responses.add(responses.GET, url, json={'ok': True}, status=200)
    resp = client.get(url)
    assert resp.status_code == 200
    assert len(responses.calls) == 3


@responses.activate
def test_no_retry_on_post():
    c = MetabaseClient('https://example.com/api', 'tok', max_retries=2)
    url = 'https://example.com/api/card/1'
    responses.add(responses.POST, url, status=503)
    with pytest.raises(requests.exceptions.RequestException):
        c.post(url, json={})
    assert len(responses.calls) == 1


@responses.activate
def test_4xx_raises():
    c = MetabaseClient('https://example.com/api', 'tok', max_retries=0)
    responses.add(
        responses.GET,
        'https://example.com/api/card/missing',
        status=404,
        json={'error': 'nope'},
    )
    with pytest.raises(requests.exceptions.RequestException):
        c.get('https://example.com/api/card/missing')
