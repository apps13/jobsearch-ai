"""Auth dependencies — resolve the current user from the access-token cookie."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserStatus
from app.repositories.user_repo import UserRepository

COOKIE_NAME = "access_token"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = UserRepository(db).get(int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user


def require_active_user(user: User = Depends(get_current_user)) -> User:
    if user.status == UserStatus.rejected:
        raise HTTPException(status_code=403, detail="Account access has been revoked")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    admin_emails = {e.lower() for e in settings.admin_emails}
    if user.email.lower() not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def enforce_generation_cap(user: User = Depends(require_active_user)) -> User:
    admin_emails = {e.lower() for e in settings.admin_emails}
    if user.email.lower() in admin_emails:
        return user
    if user.generations_used >= user.generation_limit:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Generation limit reached ({user.generations_used}/{user.generation_limit}). "
                "Contact an admin to raise your limit."
            ),
        )
    return user
