from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    code: str
    version: str
    category: str
    status: str
    chunk_count: int
    file_name: str
    uploaded_by: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DocumentChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunk_index: int
    content: str
    chapter: str
    clause: str
