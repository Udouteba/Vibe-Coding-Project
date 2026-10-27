"""管理员用户管理。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessError
from ..models import User
from ..schemas.user import UserCreate, UserUpdate
from ..utils.password import hash_password
from ..utils.validators import validate_password, validate_username


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, req: UserCreate) -> User:
    validate_username(req.username)
    validate_password(req.password)
    exists = await db.scalar(select(User).where(User.username == req.username))
    if exists:
        raise BusinessError("用户名已存在")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: int, req: UserUpdate, admin: User) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise BusinessError("用户不存在", 404)
    if user_id == admin.id:
        raise BusinessError("不能修改自己的账号")
    if req.role:
        user.role = req.role
    if req.password:
        validate_password(req.password)
        user.password_hash = hash_password(req.password)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise BusinessError("用户不存在", 404)
    if user.role == "admin":
        raise BusinessError("不能删除管理员账号")
    await db.delete(user)
    await db.commit()
