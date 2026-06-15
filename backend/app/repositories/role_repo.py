"""Data access for roles (target jobs)."""

from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, job_description: str, user_id: int) -> Role:
        role = Role(title=title, job_description=job_description, user_id=user_id)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def delete(self, role_id: int) -> None:
        role = self.db.get(Role, role_id)
        if role is not None:
            self.db.delete(role)
            self.db.commit()
