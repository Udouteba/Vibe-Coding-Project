"""密码哈希（bcrypt）。"""

import bcrypt

from ..common.exceptions import BusinessError


def hash_password(plain: str) -> str:
    if len(plain.encode("utf-8")) > 72:
        raise BusinessError("密码不能超过 72 位")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
