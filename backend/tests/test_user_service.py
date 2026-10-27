"""管理员用户管理服务层测试。"""

import pytest

from app.common.exceptions import BusinessError
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service
from app.utils.password import hash_password


async def _make_admin(db_session) -> User:
    admin = User(username="admin1", password_hash=hash_password("Pass1234"), role="admin")
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


async def test_create_user(db_session):
    await _make_admin(db_session)
    user = await user_service.create_user(
        db_session, UserCreate(username="newuser", password="Pass1234", role="student")
    )
    assert user.username == "newuser"
    assert user.role == "student"


async def test_create_user_duplicate(db_session):
    await _make_admin(db_session)
    await user_service.create_user(db_session, UserCreate(username="dup123", password="Pass1234"))
    with pytest.raises(BusinessError):
        await user_service.create_user(
            db_session, UserCreate(username="dup123", password="Pass1234")
        )


async def test_list_users(db_session):
    await _make_admin(db_session)
    users = await user_service.list_users(db_session)
    assert len(users) == 1


async def test_update_user_cannot_self(db_session):
    admin = await _make_admin(db_session)
    with pytest.raises(BusinessError):
        await user_service.update_user(db_session, admin.id, UserUpdate(role="student"), admin)


async def test_update_user_role(db_session):
    admin = await _make_admin(db_session)
    target = await user_service.create_user(
        db_session, UserCreate(username="victim", password="Pass1234", role="student")
    )
    updated = await user_service.update_user(db_session, target.id, UserUpdate(role="admin"), admin)
    assert updated.role == "admin"


async def test_delete_user(db_session):
    await _make_admin(db_session)
    target = await user_service.create_user(
        db_session, UserCreate(username="victim", password="Pass1234", role="student")
    )
    await user_service.delete_user(db_session, target.id)
    assert await db_session.get(User, target.id) is None


async def test_delete_admin_forbidden(db_session):
    admin = await _make_admin(db_session)
    with pytest.raises(BusinessError):
        await user_service.delete_user(db_session, admin.id)


async def test_delete_unknown(db_session):
    await _make_admin(db_session)
    with pytest.raises(BusinessError):
        await user_service.delete_user(db_session, 99999)
