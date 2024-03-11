import uuid
from datetime import datetime

import jwt


def generate_state() -> str:
    return str(uuid.uuid4())


def generate_nonce() -> str:
    return uuid.uuid4().hex + uuid.uuid1().hex


def get_jwt_claim(iss: str, sub: str, aud: str) -> dict[str, str | int]:
    return {
        "iss": iss,
        "sub": sub,
        "aud": aud,
        "iat": int(datetime.now().timestamp()),
        "exp": int(datetime.now().timestamp()) + 60,
    }


def encode_jwt(claims, private_key, headers) -> str:
    return jwt.encode(claims, private_key, "RS256", headers)
