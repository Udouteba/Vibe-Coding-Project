from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=3, max_length=72)
    role: str = Field(default="student")


class UserUpdate(BaseModel):
    role: str | None = None
    password: str | None = Field(default=None, min_length=3, max_length=72)
