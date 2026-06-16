"""Data access for generated cover letters (the user's history)."""

from sqlalchemy.orm import Session

from app.models.cover_letter import CoverLetter


class CoverLetterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        role_id: int,
        user_id: int,
        cover_letter: dict | None = None,
        fit_analysis: dict | None = None,
        why_this_company: str | None = None,
        resume_id: int | None = None,
    ) -> CoverLetter:
        record = CoverLetter(
            role_id=role_id,
            resume_id=resume_id,
            user_id=user_id,
            cover_letter=cover_letter,
            fit_analysis=fit_analysis,
            why_this_company=why_this_company,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list(self, user_id: int) -> list[CoverLetter]:
        return (
            self.db.query(CoverLetter)
            .filter(CoverLetter.user_id == user_id)
            .order_by(CoverLetter.created_at.desc())
            .all()
        )

    def get(self, cover_letter_id: int, user_id: int) -> CoverLetter | None:
        return (
            self.db.query(CoverLetter)
            .filter(CoverLetter.id == cover_letter_id, CoverLetter.user_id == user_id)
            .first()
        )

    def delete(self, cover_letter_id: int, user_id: int) -> bool:
        record = self.get(cover_letter_id, user_id)
        if record is None:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
