"""Pydantic schemas for the User resource (API request/response contracts)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserStatus


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    picture: str | None
    provider: str
    status: UserStatus
    created_at: datetime


class CurrentUserRead(UserRead):
    is_admin: bool
