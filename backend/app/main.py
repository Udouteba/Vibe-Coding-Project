"""应用入口：建表、挂载路由、静态文件、全局异常、演示账号。"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, select, text

from config import UPLOAD_DIR, VECTOR_DIR
from . import models  # noqa: F401  触发模型注册
from .api import api_router
from .common.exceptions import register_exception_handlers
from .database import Base, SessionLocal, engine
from .models import User
from .utils.password import hash_password


async def seed_demo_users() -> None:
    demos = [("admin", "admin", "admin"), ("aaa", "123", "student"), ("bbb", "123", "student")]
    async with SessionLocal() as db:
        for username, password, role in demos:
            exists = await db.scalar(select(User).where(User.username == username))
            if not exists:
                db.add(User(username=username, password_hash=hash_password(password), role=role))
        await db.commit()


def _ensure_theme_column(sync_conn) -> None:
    """为已存在的 users 表补 theme 列（create_all 不会给旧表加列）。"""
    columns = [c["name"] for c in inspect(sync_conn).get_columns("users")]
    if "theme" not in columns:
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN theme VARCHAR(16) NOT NULL DEFAULT 'light'")
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(VECTOR_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_theme_column)
    await seed_demo_users()
    yield


app = FastAPI(title="给排水智库", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# 挂载静态文件前确保目录存在（StaticFiles 默认校验目录）
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
register_exception_handlers(app)


@app.get("/")
async def health():
    return {"code": 200, "message": "给排水智库后端运行中", "data": None}
