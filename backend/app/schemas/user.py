"""Pydantic schemas for the User resource (API request/response contracts)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.user import UserStatus


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    picture: str | None
    provider: str
    status: UserStatus
    generations_used: int
    generation_limit: int
    created_at: datetime


class CurrentUserRead(UserRead):
    is_admin: bool


class UpdateGenerationLimitRequest(BaseModel):
    generation_limit: int = Field(ge=0)
