from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PresetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    document_ids: list[int] = Field(default_factory=list)


class PresetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    document_ids: list
    created_at: datetime | None = None
