from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "student"


class UserUpdate(BaseModel):
    role: str | None = None
    password: str | None = None
