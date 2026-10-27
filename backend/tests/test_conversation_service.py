"""会话服务层测试：CRUD、越权、排序。"""

from datetime import datetime, timedelta

import pytest

from app.common.exceptions import BusinessError
from app.models import Conversation, User
from app.schemas.conversation import ConversationUpdate
from app.services import conversation_service
from app.utils.password import hash_password


async def _make_user(db_session, name="user01") -> User:
    user = User(username=name, password_hash=hash_password("Pass1234"), role="student")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_create_and_list(db_session):
    user = await _make_user(db_session)
    await conversation_service.create_conversation(db_session, user.id, "标题")
    convs = await conversation_service.list_conversations(db_session, user.id)
    assert len(convs) == 1
    assert convs[0]["title"] == "标题"


async def test_sorting_pinned_and_recent(db_session):
    """置顶在前；同组内按更新时间倒序（最近在前）。"""
    user = await _make_user(db_session)
    base = datetime(2026, 1, 1, 12, 0, 0)
    c_old = Conversation(user_id=user.id, title="旧", created_at=base, updated_at=base)
    c_pinned = Conversation(
        user_id=user.id,
        title="置顶",
        is_pinned=True,
        created_at=base,
        updated_at=base + timedelta(minutes=1),
    )
    c_new = Conversation(
        user_id=user.id,
        title="新",
        created_at=base,
        updated_at=base + timedelta(minutes=2),
    )
    db_session.add_all([c_old, c_pinned, c_new])
    await db_session.commit()

    titles = [
        c["title"] for c in await conversation_service.list_conversations(db_session, user.id)
    ]
    assert titles == ["置顶", "新", "旧"]


async def test_get_or_create_existing(db_session):
    user = await _make_user(db_session)
    conv = await conversation_service.create_conversation(db_session, user.id, None)
    same = await conversation_service.get_or_create(db_session, user.id, conv["id"], "新消息")
    assert same.id == conv["id"]


async def test_get_or_create_new_title_truncated(db_session):
    user = await _make_user(db_session)
    msg = "一二三四五六七八九十" * 3  # 30 字，超过 20 字触发截断
    conv = await conversation_service.get_or_create(db_session, user.id, None, msg)
    assert conv.title == msg[:20] + "…"
    assert len(conv.title) == 21


async def test_get_messages_cross_user(db_session):
    u1 = await _make_user(db_session, "user01")
    u2 = await _make_user(db_session, "user02")
    conv = await conversation_service.create_conversation(db_session, u1.id, "u1的会话")
    with pytest.raises(BusinessError):
        await conversation_service.get_messages(db_session, u2.id, conv["id"])


async def test_update_cross_user(db_session):
    u1 = await _make_user(db_session, "user01")
    u2 = await _make_user(db_session, "user02")
    conv = await conversation_service.create_conversation(db_session, u1.id, "会话")
    with pytest.raises(BusinessError):
        await conversation_service.update_conversation(
            db_session, u2.id, conv["id"], ConversationUpdate(title="越权改名")
        )
