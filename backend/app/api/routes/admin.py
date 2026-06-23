"""Admin routes — list users and approve/reject pending accounts."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import UserStatus
from app.repositories.user_repo import UserRepository
from app.schemas.user import UpdateGenerationLimitRequest, UserRead

router = APIRouter(
    prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/users", response_model=list[UserRead])
def list_users(status: UserStatus | None = Query(default=None), db: Session = Depends(get_db)):
    return UserRepository(db).list(status)


@router.post("/users/{user_id}/approve", response_model=UserRead)
def approve_user(user_id: int, db: Session = Depends(get_db)):
    user = UserRepository(db).update_status(user_id, UserStatus.approved)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/reject", response_model=UserRead)
def reject_user(user_id: int, db: Session = Depends(get_db)):
    user = UserRepository(db).update_status(user_id, UserStatus.rejected)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}/limit", response_model=UserRead)
def update_generation_limit(
    user_id: int, payload: UpdateGenerationLimitRequest, db: Session = Depends(get_db)
):
    user = UserRepository(db).set_generation_limit(user_id, payload.generation_limit)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
