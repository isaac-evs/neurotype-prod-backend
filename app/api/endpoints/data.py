from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import csv
import io

from app.api import deps
from app.models.user import User
from app.services import note_service

router = APIRouter()

@router.get("/export", summary="Export user data")
def export_data(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    notes = note_service.get_notes_by_user(db, user_id=current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "text", "created_at"])
    for note in notes:
        writer.writerow([note.id, note.text, note.created_at])
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=notes.csv"
    return response
