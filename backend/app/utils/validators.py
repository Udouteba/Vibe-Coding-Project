"""用户名与密码规则校验（注册 / 管理员建号 / 改密共用）。"""

import re

from ..common.exceptions import BusinessError

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
_PASSWORD_RE = re.compile(r"^[A-Za-z0-9_]+$")


def validate_username(username: str) -> None:
    if not (5 <= len(username) <= 20):
        raise BusinessError("用户名长度需为 5~20 个字符")
    if not _USERNAME_RE.fullmatch(username):
        raise BusinessError("用户名只能包含英文字母、数字、下划线")


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise BusinessError("密码至少 8 位")
    if len(password) > 72:
        raise BusinessError("密码不能超过 72 位")
    if not _PASSWORD_RE.fullmatch(password):
        raise BusinessError("密码只能包含英文字母、数字、下划线")
    kinds = sum(
        [
            bool(re.search(r"[A-Z]", password)),
            bool(re.search(r"[a-z]", password)),
            bool(re.search(r"[0-9]", password)),
        ]
    )
    if kinds < 2:
        raise BusinessError("密码需包含大写字母、小写字母、数字中的至少两类")
