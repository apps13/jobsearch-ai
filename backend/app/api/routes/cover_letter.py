"""Cover-letter routes — generate (and persist) a letter, and list history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import enforce_generation_cap, require_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.cover_letter import CoverLetterRead, GenerateCoverLetterRequest
from app.services.generator import CoverLetterService

router = APIRouter(
    prefix="/api/cover-letter",
    tags=["cover-letter"],
    dependencies=[Depends(require_active_user)],
)


@router.post("", response_model=CoverLetterRead)
def generate(
    req: GenerateCoverLetterRequest,
    db: Session = Depends(get_db),
    user: User = Depends(enforce_generation_cap),
):
    service = CoverLetterService(db)
    try:
        return service.generate(req, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[CoverLetterRead])
def history(db: Session = Depends(get_db), user: User = Depends(require_active_user)):
    return CoverLetterService(db).history(user.id)


@router.delete("/{cover_letter_id}", status_code=204)
def delete_cover_letter(
    cover_letter_id: int, db: Session = Depends(get_db), user: User = Depends(require_active_user)
):
    deleted = CoverLetterService(db).delete_history_entry(cover_letter_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cover letter not found")
