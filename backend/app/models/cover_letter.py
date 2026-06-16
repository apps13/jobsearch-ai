"""
CoverLetter ORM model — one generated cover letter + fit analysis.

This table is the user's generation history. The generated content is stored as
JSON exactly as produced; the API serializes it into structured schemas on read.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # Nullable: a generation may use pasted resume text rather than a saved resume.
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"), nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    cover_letter: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fit_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    why_this_company: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    resume = relationship("Resume")
    role = relationship("Role")
