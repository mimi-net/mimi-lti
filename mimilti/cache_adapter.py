import datetime
import functools
from collections import OrderedDict
from collections.abc import Iterable, Hashable
import requests
from collections.abc import Callable
from requests.adapters import HTTPAdapter


class LruCache:
    """Lru Cache

    Usage::
      >>> import mimilti.cache_adapter.LruCache
      >>> lru_cache = LruCache()
      >>> @lru_cache.ttl_lru_cache # without expires
      >>> def get_x(x: int) -> int:
      >>>    return x
      >>> @lru_cache.ttl_lru_cache(datetime.timedelta(hours=1)) #with expires
      >>> def get_y(y: int) -> int:
      >>>    return y
    :param max_size: int: Lru Cache Max Size"""

    def __init__(self, max_size: int = 256):
        self.max_size = max_size
        self._cache = OrderedDict()

    def __len__(self):
        return len(self._cache)

    def clear(self):
        self._cache.clear()

    def ttl_lru_cache[
        T, **P
    ](self, expires: datetime.timedelta | None = None) -> Callable[
        [Callable[(P.args, P.kwargs), T]], Callable[(P.args, P.kwargs), T]
    ]:
        """Lru Cache decorator
         :param expires: datetime.timedelta | None: Result caching time.
        :return: Inner decorator for cache
        """

        def wrapper_cache(
            func: Callable[(P.args, P.kwargs), T]
        ) -> Callable[(P.args, P.kwargs), T]:
            """Inner Lru Cache decorator.

            :param func: Callable[P, T]: Callable for processing
            :return: Callable[P, T]: The function to call.
            """

            # When expires = None, there will be a standard Lru Cache)
            # The expires parameter is unique for each function.

            @functools.wraps(func)
            def wrapped_func(*args: P.args, **kwargs: P.kwargs) -> T:
                """Inner decorator for cache.

                :param args: P.args: Positional function arguments
                :param kwargs: P.kwargs: Named function arguments
                :return: T: result of the function execution

                """

                # Turning function arguments into Hashable to get a result based on the value of the arguments
                kwargs = dict(sorted(kwargs.items()))
                kwargs_list = []
                for key in kwargs:
                    if isinstance(kwargs[key], Hashable):
                        kwargs_list.append((key, kwargs[key]))
                    elif isinstance(kwargs[key], Iterable):
                        kwargs_list.append((key, tuple(kwargs[key])))
                    else:
                        return
                kwargs_tuple = tuple(kwargs_list)
                cache_key = (args, kwargs_tuple)

                value_dict = self._cache.get(cache_key, None)

                # If the time has expired and no one accesses the value,
                # Then it will be deleted when it overflows, otherwise the value will be updated.
                if value_dict is not None:
                    expires_datetime = value_dict["expires_datetime"]
                    if expires_datetime and datetime.datetime.now() > expires_datetime:
                        self._cache.pop(cache_key, None)
                    else:
                        self._cache.move_to_end(cache_key)
                        return value_dict["value"]

                start_time = datetime.datetime.now()
                value = func(*args, **kwargs)
                expires_datetime = None if expires is None else start_time + expires
                dct = {"value": value, "expires_datetime": expires_datetime}
                self._cache[cache_key] = dct

                if len(self._cache) > self.max_size:
                    self._cache.popitem(False)

                return value

            return wrapped_func

        return wrapper_cache


class MimiSession(requests.Session):
    """A request.Session with support for caching using lru cache with ttl.

    Adds functionality for caching requests.

    Usage::
      >>> from mimilti.cache_adapter import MimiSession, CacheAdapter
      >>> s = MimiSession()
      >>> expires = datetime.timedelta(seconds=3600)
      >>> cache_adapter = CacheAdapter()
      >>> s.mount("http://localhost/moodle/mod/lti/token.php", cache_adapter)
      >>> s.get('http://localhost/moodle/mod/lti/token.php')
    """

    def __init__(self):
        super().__init__()
        self._lru_cache = LruCache(128)
        self._ttl_cache = self._lru_cache.ttl_lru_cache

    def request(self, *args, **kwargs):

        if len(args) > 1:
            url = args[1]
        else:
            url = kwargs["url"]

        adapter = self.get_adapter(url=url)

        if isinstance(adapter, CacheAdapter):
            expires = adapter.expires
            return self._ttl_cache(expires)(super().request)(*args, **kwargs)

        return super().request(*args, **kwargs)


class CacheAdapter(HTTPAdapter):
    """HTTPAdapter for caching requests

    :param expires: datetime.timedelta: Request caching time

    """

    def __init__(self, expires: datetime.timedelta):
        super().__init__()
        self._expires = expires

    @property
    def expires(self) -> datetime.timedelta:
        """Getter for expires

        :return: datetime.timedelta: Request caching time"""
        return self._expires

    @expires.setter
    def expires(self, expires: datetime.timedelta) -> None:
        """Setter for expires

        :param expires: datetime.timedelta: Request caching time"""
        self._expires = expires
