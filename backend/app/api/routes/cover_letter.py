"""Cover-letter routes — generate (and persist) a letter, and list history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.cover_letter import CoverLetterRead, GenerateCoverLetterRequest
from app.services.generator import CoverLetterService

router = APIRouter(prefix="/api/cover-letter", tags=["cover-letter"])


@router.post("", response_model=CoverLetterRead)
def generate(req: GenerateCoverLetterRequest, db: Session = Depends(get_db)):
    service = CoverLetterService(db)
    try:
        return service.generate(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[CoverLetterRead])
def history(db: Session = Depends(get_db)):
    return CoverLetterService(db).history()


@router.delete("/{cover_letter_id}", status_code=204)
def delete_cover_letter(cover_letter_id: int, db: Session = Depends(get_db)):
    deleted = CoverLetterService(db).delete_history_entry(cover_letter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cover letter not found")
