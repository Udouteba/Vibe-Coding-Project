from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.response import ok
from ..database import get_db
from ..dependencies.auth import get_current_admin
from ..models import User
from ..schemas.auth import UserOut
from ..schemas.user import UserCreate, UserUpdate
from ..services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    users = await user_service.list_users(db)
    return ok([UserOut.model_validate(u).model_dump() for u in users])


@router.post("")
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = await user_service.create_user(db, req)
    return ok(UserOut.model_validate(user).model_dump(), "创建成功")


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    req: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = await user_service.update_user(db, user_id, req, admin)
    return ok(UserOut.model_validate(user).model_dump(), "更新成功")


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    await user_service.delete_user(db, user_id)
    return ok(message="删除成功")
