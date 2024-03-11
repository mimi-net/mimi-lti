import typing as tp

from mimilti.lms_pool import LmsRequestsPool
from mimilti.config import Config
from mimilti.data_storage import DataStorage
from mimilti.utils.jwt_utils import encode_jwt, get_jwt_claim


class LMSClient:
    def __init__(self, data_service: DataStorage, config: Config):
        self._data_service = data_service
        self._config = config
        self._tool = config.get_tool(self._data_service.iss, self._data_service.aud)
        self._access_token = {"access_token": "", "scope": ""}

    def get_current_lms(self):
        return self._data_service.iss

    def get_current_tool(self):
        return self._tool

    @staticmethod
    def _get_auth_param(scope, client_assertion):
        return {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
            "scope": scope,
        }

    def _get_token_scopes(self):
        return set(self._access_token["scope"].split(" "))

    def get_access_token(self, scopes: tp.Sequence[str]):

        client_id = self._tool.get_client_id()
        auth_url = self._config.get_token_url(self._data_service.iss)

        claims = get_jwt_claim(client_id, client_id, auth_url)
        rsa_key, kid = self._config.get_keys_and_kid()
        jwt_encode = encode_jwt(claims, rsa_key.private_key, {"kid": kid})
        auth_param = self._get_auth_param(" ".join(scopes), jwt_encode)
        response = self.send_request_to_lms(
            scopes=None,
            url=auth_url,
            accept="application/json",
            content_type="application/x-www-form-urlencoded",
            request_type="POST",
            data=auth_param,
        )

        self._access_token = self.get_json(response)
        return self._access_token

    def send_request_to_lms(
        self,
        scopes: tp.Sequence[str] | None,
        url: str,
        accept: str,
        content_type: str,
        request_type: str,
        data: None | dict | str = None,
        need_token: bool = False,
    ):
        headers = {
            "Accept": accept,
            "Content-Type": content_type,
        }

        if need_token and (scopes is None or len(scopes) <= 0):
            return None
        if need_token:
            if set(scopes) <= self._get_token_scopes():
                access_token = self._access_token["access_token"]
            else:
                self._access_token = self.get_access_token(scopes)
                access_token = self._access_token["access_token"]

            headers["Authorization"] = "Bearer " + access_token

        session = LmsRequestsPool.session

        match request_type:
            case "GET":
                response = session.get(url, headers=headers)
            case "POST":
                response = session.post(url, data=data, headers=headers)
            case _:
                raise Exception(f"Method not supported: {request_type}")

        response.raise_for_status()

        return response

    @staticmethod
    def get_json(response):
        return response.json()
