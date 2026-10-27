"""注册 / 登录 / 修改密码。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessError
from ..models import User
from ..schemas.auth import UserOut
from ..utils.jwt import create_token
from ..utils.password import hash_password, verify_password
from ..utils.validators import validate_password, validate_username


async def register(db: AsyncSession, username: str, password: str) -> User:
    validate_username(username)
    validate_password(password)
    exists = await db.scalar(select(User).where(User.username == username))
    if exists:
        raise BusinessError("用户名已存在")
    user = User(username=username, password_hash=hash_password(password), role="student")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, username: str, password: str) -> dict:
    user = await db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise BusinessError("用户名或密码错误", 401)
    token = create_token(user.id)
    return {
        "token": token,
        "user": UserOut.model_validate(user).model_dump(),
    }


async def change_password(
    db: AsyncSession, user: User, old_password: str, new_password: str
) -> None:
    if not verify_password(old_password, user.password_hash):
        raise BusinessError("原密码错误")
    validate_password(new_password)
    user.password_hash = hash_password(new_password)
    await db.commit()


async def update_theme(db: AsyncSession, user: User, theme: str) -> None:
    if theme not in ("light", "dark"):
        raise BusinessError("主题取值无效")
    user.theme = theme
    await db.commit()
