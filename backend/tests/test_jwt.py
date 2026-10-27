"""JWT 生成与解析。"""

import time

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.utils.jwt import create_token, decode_token
from config import settings


def test_roundtrip():
    payload = decode_token(create_token(42))
    assert payload["user_id"] == 42


def test_invalid_token():
    with pytest.raises(HTTPException) as e:
        decode_token("invalid.token.here")
    assert e.value.status_code == 401


def test_expired_token():
    token = pyjwt.encode(
        {"user_id": 1, "exp": int(time.time()) - 10},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(HTTPException) as e:
        decode_token(token)
    assert e.value.status_code == 401
