"""检索预设服务层测试。"""

import pytest

from app.common.exceptions import BusinessError
from app.models import User
from app.schemas.preset import PresetCreate
from app.services import preset_service
from app.utils.password import hash_password


async def _make_user(db_session, name="user01") -> User:
    user = User(username=name, password_hash=hash_password("Pass1234"), role="student")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_create_and_list(db_session):
    user = await _make_user(db_session)
    await preset_service.create_preset(
        db_session, user.id, PresetCreate(name="给水范围", document_ids=[1, 2])
    )
    presets = await preset_service.list_presets(db_session, user.id)
    assert len(presets) == 1
    assert presets[0].document_ids == [1, 2]


async def test_delete_ok(db_session):
    user = await _make_user(db_session)
    preset = await preset_service.create_preset(db_session, user.id, PresetCreate(name="预设"))
    await preset_service.delete_preset(db_session, user.id, preset.id)
    assert await preset_service.list_presets(db_session, user.id) == []


async def test_delete_cross_user(db_session):
    u1 = await _make_user(db_session, "user01")
    u2 = await _make_user(db_session, "user02")
    preset = await preset_service.create_preset(db_session, u1.id, PresetCreate(name="预设"))
    with pytest.raises(BusinessError):
        await preset_service.delete_preset(db_session, u2.id, preset.id)
