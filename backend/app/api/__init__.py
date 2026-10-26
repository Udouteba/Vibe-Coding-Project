from fastapi import APIRouter

from . import auth, categories, chat, conversations, documents, presets, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(categories.router)
api_router.include_router(presets.router)
api_router.include_router(conversations.router)
api_router.include_router(chat.router)
