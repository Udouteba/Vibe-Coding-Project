"""会话与消息：创建 / 列表 / 重命名 / 置顶 / 归档 / 删除 / 历史消息。"""
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessError
from ..models import Conversation, Message
from ..schemas.conversation import ConversationUpdate


async def get_or_create(
    db: AsyncSession, user_id: int, conversation_id: int | None, first_message: str
) -> Conversation:
    if conversation_id:
        conv = await db.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            raise BusinessError("会话不存在", 404)
        return conv
    title = first_message[:20] + "…" if len(first_message) > 20 else first_message
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def create_conversation(db: AsyncSession, user_id: int, title: str | None) -> dict:
    conv = Conversation(user_id=user_id, title=title or "新对话")
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return _to_dict(conv, None)


async def list_conversations(db: AsyncSession, user_id: int) -> list[dict]:
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id)
    )
    convs = [c for c in result.scalars().all() if not c.is_archived]

    last_by_conv: dict[int, str] = {}
    ids = [c.id for c in convs]
    if ids:
        msg_result = await db.execute(
            select(Message).where(Message.conversation_id.in_(ids)).order_by(Message.id)
        )
        for m in msg_result.scalars().all():
            last_by_conv[m.conversation_id] = m.content

    convs.sort(key=lambda c: (not c.is_pinned, c.updated_at or c.created_at), reverse=False)
    return [_to_dict(c, last_by_conv.get(c.id)) for c in convs]


async def update_conversation(
    db: AsyncSession, user_id: int, conv_id: int, req: ConversationUpdate
) -> dict:
    conv = await _own(db, user_id, conv_id)
    if req.title is not None:
        conv.title = req.title
    if req.is_pinned is not None:
        conv.is_pinned = req.is_pinned
    if req.is_archived is not None:
        conv.is_archived = req.is_archived
    conv.updated_at = datetime.now()
    await db.commit()
    await db.refresh(conv)
    return _to_dict(conv, None)


async def delete_conversation(db: AsyncSession, user_id: int, conv_id: int) -> None:
    conv = await _own(db, user_id, conv_id)
    await db.execute(delete(Message).where(Message.conversation_id == conv_id))
    await db.delete(conv)
    await db.commit()


async def list_messages(db: AsyncSession, conversation_id: int) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id)
    )
    return list(result.scalars().all())


async def get_messages(db: AsyncSession, user_id: int, conv_id: int) -> list[Message]:
    await _own(db, user_id, conv_id)
    return await list_messages(db, conv_id)


async def touch(db: AsyncSession, conversation_id: int) -> None:
    conv = await db.get(Conversation, conversation_id)
    if conv:
        conv.updated_at = datetime.now()
        await db.commit()


async def _own(db: AsyncSession, user_id: int, conv_id: int) -> Conversation:
    conv = await db.get(Conversation, conv_id)
    if conv is None or conv.user_id != user_id:
        raise BusinessError("会话不存在", 404)
    return conv


def _to_dict(conv: Conversation, last_message: str | None) -> dict:
    return {
        "id": conv.id,
        "title": conv.title,
        "is_pinned": conv.is_pinned,
        "is_archived": conv.is_archived,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "last_message": last_message,
    }
