import dataclasses
from base64 import b64decode, urlsafe_b64decode
from datetime import timedelta

import jwt
from Crypto.PublicKey.RSA import construct
from marshmallow import Schema, fields, post_load

from mimilti.cache_adapter import LruCache
from mimilti.lms_client import LMSClient
from mimilti.lms_pool import LmsRequestsPool
from mimilti.config import Config


@dataclasses.dataclass
class Key:
    kty: str
    alg: str | None
    use: str
    public_key: bytes


class KeySchema(Schema):
    kty = fields.String()
    alg = fields.Raw()
    use = fields.Raw()
    e = fields.Raw()
    n = fields.Raw()
    kid = fields.Raw()
    public_key = fields.Raw()

    @post_load
    def make_user(self, data, **kwargs):
        _ = kwargs
        return Key(
            kty=data["kty"],
            alg=data["alg"],
            use=data["use"],
            public_key=data["public_key"],
        )


class LmsJwkClient:
    KeySchema = KeySchema()

    # The magic constant is 5 to ensure the relevance of the results
    result_expires_time = (
        LmsRequestsPool.default_jwks_endpoint_expires_time - timedelta(seconds=5)
    )

    def __init__(self, data_service, config: Config):
        self._data_service = data_service
        self._lms_client = LMSClient(data_service, config)
        self._keys = {}
        self._config = config

    @staticmethod
    @LruCache(max_size=32).ttl_lru_cache(expires=result_expires_time)
    def _generate_public_key(e: str, n: str, kty: str = "RSA") -> bytes:

        if kty == "RSA":
            e = int.from_bytes(b64decode(e + "===="))
            n = int.from_bytes(urlsafe_b64decode(n + "===="))
            public_key = construct((n, e)).public_key().exportKey()
            return public_key

    def _get_key_from_jwks_endpoint(self, kid: str, endpoint: str) -> Key:
        response = self._lms_client.send_request_to_lms(
            scopes=None,
            url=endpoint,
            accept="application/json",
            content_type="application/json",
            request_type="GET",
            data=None,
            need_token=False,
        )
        return self._get_public_key(response, kid)

    def _get_public_key(self, response, kid) -> Key:
        keys_dict = self._lms_client.get_json(response)
        keys = keys_dict.get("keys", None)
        for key in keys:
            public_key = self._generate_public_key(key["e"], key["n"], key["kty"])
            key["public_key"] = public_key

            key = LmsJwkClient.KeySchema.load(key)

            self._keys[kid] = key

        return self._get_public_key_with_kid(kid)

    def _get_public_key_with_kid(self, kid) -> Key:

        if kid not in self._keys:
            raise Exception("Key not found")

        return self._keys[kid]

    def decode_jwt_token(self, id_token: str):
        headers = jwt.get_unverified_header(id_token)

        kid = headers["kid"]
        endpoint = self._config.generate_template_endpoint(
            self._data_service.iss, self._data_service.aud
        )
        key = self._get_key_from_jwks_endpoint(kid, endpoint)

        if key.kty != "RSA":
            raise Exception("Algorithm not supported")

        if key.alg is None:
            raise Exception("Key is not signed")

        algorithms = [key.alg]

        data = jwt.decode(
            id_token,
            key.public_key,
            algorithms=algorithms,
            audience=self._data_service.aud,
            verify_signature=True,
            verify_aud=True,
        )

        return data
