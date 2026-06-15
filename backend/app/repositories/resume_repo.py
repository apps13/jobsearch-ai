"""Data access for resumes. The only place that knows how resumes are stored."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, label: str, content: str, user_id: int) -> Resume:
        resume = Resume(label=label, content=content, user_id=user_id)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get(self, resume_id: int, user_id: int) -> Resume | None:
        return (
            self.db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == user_id)
            .first()
        )

    def get_by_label(self, label: str, user_id: int) -> Resume | None:
        return (
            self.db.query(Resume)
            .filter(func.lower(Resume.label) == label.lower(), Resume.user_id == user_id)
            .first()
        )

    def list(self, user_id: int) -> list[Resume]:
        return (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .all()
        )

    def delete(self, resume_id: int, user_id: int) -> bool:
        resume = self.get(resume_id, user_id)
        if resume is None:
            return False
        self.db.delete(resume)
        self.db.commit()
        return True
