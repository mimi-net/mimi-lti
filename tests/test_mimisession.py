import datetime
import time
from unittest.mock import patch
import requests
from mimilti.cache_adapter import MimiSession, CacheAdapter, LruCache


def get_unique_session():
    from random import randbytes

    unique_response = requests.Response()
    unique_response._content = randbytes(12)
    unique_response.status_code = 200

    return unique_response


@patch.object(requests.Session, "request")
def test_cache_send_request(mock_method):
    mimisession = MimiSession()
    mock_method.side_effect = lambda *args, **kwargs: get_unique_session()

    expires = datetime.timedelta(seconds=1)
    mimisession.mount("https://8.8.8.8", CacheAdapter(expires=expires))
    response = mimisession.get("https://8.8.8.8")

    for i in range(1):
        assert response is mimisession.get("https://8.8.8.8")

    time.sleep(expires.total_seconds())

    new_response = mimisession.get("https://8.8.8.8")
    assert response is not mimisession.get("https://8.8.8.8")

    assert new_response is mimisession.get("https://8.8.8.8")


def test_cache_adapter_prefix():
    mimisession = MimiSession()

    expires = datetime.timedelta(seconds=3)
    adapter = CacheAdapter(expires=expires)

    mimisession.mount("https://8.8.8.8", adapter)

    google_response = mimisession.get("https://8.8.8.8")
    google_bebra_response = mimisession.get("https://8.8.8.8/bebra")

    assert google_response is not google_bebra_response

    data = {"1": 1, "2": 2}

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    second_google_response = mimisession.post(
        "https://8.8.8.8", data=data, headers=headers
    )
    assert second_google_response is not google_response

    third_google_response = mimisession.post(
        "https://8.8.8.8", headers=headers, data=data
    )
    assert third_google_response is second_google_response

    del headers["Accept"]
    fourth_google_response = mimisession.post(
        "https://8.8.8.8", headers=headers, data=data
    )
    assert fourth_google_response is not third_google_response


def test_lru_cache_size():
    max_size = 5
    cache = LruCache(max_size=max_size)
    assert len(cache) == 0

    @cache.ttl_lru_cache()
    def numbers(n: int) -> int:
        return n

    for i in range(5):
        _ = numbers(i)
        assert len(cache) == i + 1

    _ = numbers(6)
    _ = numbers(7)
    _ = numbers(8)

    assert len(cache) == 5

    cache.clear()

    def x2(x: int) -> int:
        return 2 * x

    seconds = 1
    x2 = cache.ttl_lru_cache(datetime.timedelta(seconds=seconds))(x2)
    x2(1)
    assert len(cache) == 1
    x2(2)
    assert len(cache) == 2
    time.sleep(seconds)
    x2(1), x2(2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
