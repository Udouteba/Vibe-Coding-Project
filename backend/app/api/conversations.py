from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.response import ok
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    MessageOut,
)
from ..services import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    convs = await conversation_service.list_conversations(db, user.id)
    return ok(convs)


@router.post("")
async def create_conversation(
    req: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = await conversation_service.create_conversation(db, user.id, req.title)
    return ok(conv, "创建成功")


@router.patch("/{conv_id}")
async def update_conversation(
    conv_id: int,
    req: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = await conversation_service.update_conversation(db, user.id, conv_id, req)
    return ok(conv, "更新成功")


@router.delete("/{conv_id}")
async def delete_conversation(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await conversation_service.delete_conversation(db, user.id, conv_id)
    return ok(message="删除成功")


@router.get("/{conv_id}/messages")
async def list_messages(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    msgs = await conversation_service.get_messages(db, user.id, conv_id)
    return ok([MessageOut.model_validate(m).model_dump() for m in msgs])
