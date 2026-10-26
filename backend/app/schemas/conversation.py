from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    is_pinned: bool
    is_archived: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_message: str | None = None


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    is_pinned: bool | None = None
    is_archived: bool | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    citations: list | None = None
    low_confidence: bool = False
    created_at: datetime | None = None
