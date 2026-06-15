"""Pydantic schemas for the Resume resource (API request/response contracts)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeCreate(BaseModel):
    label: str
    content: str


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    content: str
    created_at: datetime
