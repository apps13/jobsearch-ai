"""
Pydantic schemas for cover-letter generation.

These define the API contract and the exact shape the LLM must return — replacing
the loose `dict` typing from the original implementation.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CoverLetterBody(BaseModel):
    greeting: str
    opening_paragraph: str
    body_paragraph_1: str
    body_paragraph_2: str
    closing_paragraph: str
    sign_off: str


class FitAnalysis(BaseModel):
    match_score: int
    matched_skills: list[str]
    gaps: list[str]
    recommendation: str


class GenerateCoverLetterRequest(BaseModel):
    """Provide either a saved resume_id or pasted resume_text, plus the role."""

    resume_id: int | None = None
    resume_text: str | None = None
    role_title: str
    job_description: str


class CoverLetterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int | None
    role_id: int
    cover_letter: CoverLetterBody
    fit_analysis: FitAnalysis
    created_at: datetime
