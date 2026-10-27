"""注册 / 登录 / 改密 / 主题 服务层测试（SQLite）。"""

import pytest

from app.common.exceptions import BusinessError
from app.services import auth_service


async def test_register_and_login(db_session):
    user = await auth_service.register(db_session, "alice1", "Pass1234")
    assert user.username == "alice1"
    assert user.role == "student"

    result = await auth_service.login(db_session, "alice1", "Pass1234")
    assert result["token"]
    assert result["user"]["username"] == "alice1"


async def test_register_duplicate(db_session):
    await auth_service.register(db_session, "bob12", "Pass1234")
    with pytest.raises(BusinessError):
        await auth_service.register(db_session, "bob12", "Pass1234")


async def test_login_wrong_password(db_session):
    await auth_service.register(db_session, "carol1", "Pass1234")
    with pytest.raises(BusinessError):
        await auth_service.login(db_session, "carol1", "Wrong123")


async def test_login_unknown_user(db_session):
    with pytest.raises(BusinessError):
        await auth_service.login(db_session, "nobody", "Pass1234")


async def test_change_password(db_session):
    user = await auth_service.register(db_session, "dave12", "Pass1234")
    await auth_service.change_password(db_session, user, "Pass1234", "NewPass12")
    await auth_service.login(db_session, "dave12", "NewPass12")


async def test_change_password_wrong_old(db_session):
    user = await auth_service.register(db_session, "erin12", "Pass1234")
    with pytest.raises(BusinessError):
        await auth_service.change_password(db_session, user, "WrongOld", "NewPass12")


async def test_update_theme(db_session):
    user = await auth_service.register(db_session, "frank1", "Pass1234")
    await auth_service.update_theme(db_session, user, "dark")
    assert user.theme == "dark"
    with pytest.raises(BusinessError):
        await auth_service.update_theme(db_session, user, "blue")
