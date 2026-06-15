"""Data access for resumes. The only place that knows how resumes are stored."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, label: str, content: str) -> Resume:
        resume = Resume(label=label, content=content)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get(self, resume_id: int) -> Resume | None:
        return self.db.get(Resume, resume_id)

    def get_by_label(self, label: str) -> Resume | None:
        return (
            self.db.query(Resume)
            .filter(func.lower(Resume.label) == label.lower())
            .first()
        )

    def list(self) -> list[Resume]:
        return self.db.query(Resume).order_by(Resume.created_at.desc()).all()

    def delete(self, resume_id: int) -> bool:
        resume = self.db.get(Resume, resume_id)
        if resume is None:
            return False
        self.db.delete(resume)
        self.db.commit()
        return True
