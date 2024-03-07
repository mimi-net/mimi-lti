from urllib.parse import urlencode

from mimilti.config import Config
from mimilti.jwk import LmsJwkClient
from mimilti.utils.jwt_utils import generate_nonce, generate_state
from mimilti.data_storage import SessionStorage
from mimilti.exceptions import (
    RequestIssuerNotTrustedError,
    RequestStateError,
    RequestNonceError,
)


class LtiRequestObject:
    def __init__(self, request_data, session_service: SessionStorage, config: Config):
        self._session_service = session_service
        self._iss = request_data.get("iss", None)
        if self._iss is not None and not config.is_trusted_issuer(self._iss):
            raise RequestIssuerNotTrustedError(self._iss)
        self._config = config
        self._target_link_uri = request_data.get("target_link_uri", None)
        self._login_hint = request_data.get("login_hint", None)
        self._lti_message_hint = request_data.get("lti_message_hint", None)
        self._client_id = request_data.get("client_id", None)
        self._lti_deployment_id = request_data.get("lti_deployment_id", None)
        self._state = request_data.get("state", None)
        self._token = request_data.get("id_token", None)
        self._jwk_client = LmsJwkClient(self._session_service, self._config)

    @staticmethod
    def is_lti_request(request_data: dict):
        return (
            "iss" in request_data
            and "target_link_uri" in request_data
            and "login_hint" in request_data
            and "lti_message_hint" in request_data
            and "client_id" in request_data
            and "lti_deployment_id" in request_data
        )

    def get_target_link_uri(self) -> str | None:
        return self._target_link_uri

    def get_issuer(self) -> str | None:
        return self._iss

    def get_client_id(self) -> str | None:
        return self._client_id

    def _get_auth_params(self) -> dict[str, str]:
        nonce = generate_nonce()
        self._session_service.save_param_to_session(nonce, "lti-nonce")

        state = generate_state()
        self._session_service.save_param_to_session(state, "lti-state")

        # https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
        return {
            "scope": "openid",
            "response_type": "id_token",
            "client_id": self._client_id,
            "redirect_uri": self._target_link_uri,
            "login_hint": self._login_hint,
            "lti_message_hint": self._lti_message_hint,
            "state": state,
            "response_mode": "form_post",
            "nonce": nonce,
        }

    def get_redirect_url(self) -> str:
        base_auth_url = self._config.get_login_url(self._iss)
        param_str = urlencode(self._get_auth_params())
        return base_auth_url + "?" + param_str

    def get_token(self) -> str:
        state_validate_result = self._session_service.session_validate(
            self._state, "lti-state"
        )
        self._session_service.remove_param_from_session("lti-state")

        if not state_validate_result:
            raise RequestStateError

        data = self._jwk_client.decode_jwt_token(self._token)

        nonce_validate_result = self._session_service.session_validate(
            data["nonce"], "lti-nonce"
        )

        self._session_service.remove_param_from_session("lti-nonce")

        if not nonce_validate_result:
            raise RequestNonceError

        return data
