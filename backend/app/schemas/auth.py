from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    theme: str | None = None
    created_at: datetime | None = None


class TokenOut(BaseModel):
    token: str
    user: UserOut


class ThemeUpdate(BaseModel):
    theme: str
