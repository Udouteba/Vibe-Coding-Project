from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.chat import ChatRequest
from ..services import agent_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest, user: User = Depends(get_current_user)):
    return StreamingResponse(
        agent_service.stream_ask(user.id, req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
