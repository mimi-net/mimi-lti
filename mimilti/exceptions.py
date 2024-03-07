class RequestIssuerNotTrustedError(Exception):
    def __init__(self, issuer: str):
        self.issuer = issuer

    def __str__(self):
        return f"LtiRequestIssuerError: {self.issuer} is not trusted issuer"


class RequestNonceError(Exception):

    def __str__(self):
        return "LtiRequestNonceError: invalid jwt nonce"


class RequestTargetUriError(Exception):

    def __str__(self):
        return "LtiRequestTargetUriError: Missing target_link_uri parameter"


class RequestNonValidTokenError(Exception):

    def __str__(self):
        return "LtiRequestNonValidTokenError: Non valid jwt token"


class RequestStateError(Exception):

    def __str__(self):
        return "LtiRequestStateError: Invalid session state"
