"""Import all models so they register on the shared Base metadata."""

from app.models.cover_letter import CoverLetter
from app.models.resume import Resume
from app.models.role import Role
from app.models.user import User

__all__ = ["Resume", "Role", "CoverLetter", "User"]
