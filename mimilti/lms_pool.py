import datetime
from requests.exceptions import InvalidSchema

from mimilti.cache_adapter import CacheAdapter, MimiSession
from mimilti.config import Config


class LmsRequestsPool:
    # A limited number of sessions to increase performance
    # (to reuse the basic TCP connection when connecting to each host),
    # while each lms creates its own session (this does not make sense now,
    # but it is useful for more flexible
    # configuration of session parameters for each lms in the future)

    issuers = {}
    session = MimiSession()

    default_token_expires_time = datetime.timedelta(minutes=30)
    default_jwks_endpoint_expires_time = datetime.timedelta(hours=6)

    @classmethod
    def start(cls, config: Config):
        cls.issuers = config.get_issuers()

        # for iss, session in sessions.items():
        #     session.mount(LtiConfig.get_token_url(iss), CacheAdapter(expires=3600))
        #     session.mount(LtiConfig.get_jwks_endpoint(iss), CacheAdapter(expires=3600 * 5))

        # Caching requests for access tokens and jwks endpoint
        for issuer in cls.issuers:
            # it is different for each lms, so far it is the standard value for moodle

            for tool in config.get_tools(issuer):
                cls.session.mount(
                    config.get_token_url(issuer),
                    CacheAdapter(cls.default_token_expires_time),
                )
                cls.session.mount(
                    tool.get_jwks_endpoint(),
                    CacheAdapter(cls.default_jwks_endpoint_expires_time),
                )

        pass

    @classmethod
    def _refresh_session(cls, issuer: str):
        pass

    @classmethod
    def get_adapter(cls, url):
        try:
            adapter = LmsRequestsPool.session.get_adapter(url)
        except InvalidSchema:
            return None
        return adapter
