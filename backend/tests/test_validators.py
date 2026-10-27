"""用户名与密码规则校验单元测试。"""

import pytest

from app.common.exceptions import BusinessError
from app.utils.validators import validate_password, validate_username


class TestValidateUsername:
    def test_ok(self):
        validate_username("abcde")  # 5 位下界
        validate_username("user_123")
        validate_username("a" * 20)  # 20 位上界

    @pytest.mark.parametrize("name", ["abcd", "a" * 21, "", "用户名", "a-b", "a b"])
    def test_invalid(self, name):
        with pytest.raises(BusinessError):
            validate_username(name)


class TestValidatePassword:
    def test_ok(self):
        validate_password("Abc12345")  # 大写 + 小写 + 数字

    def test_ok_underscore(self):
        validate_password("Abc_def1")

    def test_two_kinds_only(self):
        validate_password("abcdefg1")  # 仅小写 + 数字也合法

    def test_max_72_boundary(self):
        validate_password("aA1" + "b" * 69)  # 恰好 72 位

    @pytest.mark.parametrize(
        "pwd",
        ["a" * 7, "a" * 73, "abcdefgh", "ABCDEFGH", "12345678", "abc def1", "Abc-1234"],
    )
    def test_invalid(self, pwd):
        with pytest.raises(BusinessError):
            validate_password(pwd)
