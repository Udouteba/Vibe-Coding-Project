"""密码哈希与校验（bcrypt）。"""

import pytest

from app.common.exceptions import BusinessError
from app.utils.password import hash_password, verify_password


def test_hash_and_verify():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed)


def test_verify_wrong_password():
    hashed = hash_password("Secret123")
    assert not verify_password("Wrong123", hashed)


def test_verify_invalid_hash():
    assert not verify_password("Secret123", "not-a-valid-bcrypt-hash")


def test_hash_too_long_raises():
    with pytest.raises(BusinessError):
        hash_password("a" * 73)
