"""JWT 生成与解析。"""

import time

import jwt
from fastapi import HTTPException

from config import settings


def create_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"user_id": user_id, "exp": now + settings.JWT_EXPIRE_MINUTES * 60}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的登录凭证") from None
