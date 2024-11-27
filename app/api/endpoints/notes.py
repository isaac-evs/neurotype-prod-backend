from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, date, timedelta

from app import schemas
from app.api import deps
from app.services import note_service
from app.models.user import User
from app.models.note import Note

router = APIRouter()

@router.get("/", response_model=List[schemas.Note])
def read_notes(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    notes = note_service.get_notes_by_user_and_date(
        db, user_id=current_user.id, start_date=start_date, end_date=end_date
    )
    return notes

@router.post("/", response_model=schemas.Note)
def create_note(
    *,
    db: Session = Depends(deps.get_db),
    note_in: schemas.NoteCreate,
    current_user: User = Depends(deps.get_current_user),
):
    note = note_service.create_user_note(db, note_in, current_user.id)
    return note

@router.put("/{note_id}", response_model=schemas.Note)
def update_note(
    *,
    db: Session = Depends(deps.get_db),
    note_id: int,
    note_in: schemas.NoteUpdate,
    current_user: User = Depends(deps.get_current_user),
):
    note = note_service.get_note_by_id(db, note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    updated_note = note_service.update_user_note(db, note, note_in)
    return updated_note

@router.delete("/{note_id}", response_model=schemas.Note)
def delete_note(
    *,
    db: Session = Depends(deps.get_db),
    note_id: int,
    current_user: User = Depends(deps.get_current_user),
):
    note = note_service.get_note_by_id(db, note_id)
    if not note or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    note_service.delete_user_note(db, note)
    return note

@router.get("/daily-analysis", response_model=schemas.DailyAnalysis)
def get_daily_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    analysis_date: date,
):
    """
    Get the emotional analysis for notes on a specific date.
    """
    notes = db.query(Note).filter(
        Note.user_id == current_user.id,
        func.date(Note.created_at) == analysis_date
    ).all()

    total_counts = {
        "happy": sum(note.happy_count for note in notes),
        "calm": sum(note.calm_count for note in notes),
        "sad": sum(note.sad_count for note in notes),
        "upset": sum(note.upset_count for note in notes),
    }

    return schemas.DailyAnalysis(
        date=analysis_date,
        total_counts=total_counts,
        notes=notes
    )

@router.get("/emotions-summary", response_model=List[schemas.DailyEmotionSummary])
def get_emotions_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    start_date: date,
    end_date: date,
):
    """
    Get the prevalent emotion for each day within a date range.
    """
    # Adjust end_date to include the entire day
    end_date = end_date + timedelta(days=1)

    # Query to aggregate emotion counts per day
    emotion_summaries = db.query(
        func.date(Note.created_at).label('date'),
        func.sum(Note.happy_count).label('happy'),
        func.sum(Note.calm_count).label('calm'),
        func.sum(Note.sad_count).label('sad'),
        func.sum(Note.upset_count).label('upset'),
    ).filter(
        Note.user_id == current_user.id,
        Note.created_at >= start_date,
        Note.created_at < end_date
    ).group_by(
        func.date(Note.created_at)
    ).all()

    # Prepare the response data
    result = []
    for summary in emotion_summaries:
        emotions = {
            'happy': summary.happy or 0,
            'calm': summary.calm or 0,
            'sad': summary.sad or 0,
            'upset': summary.upset or 0
        }
        prevalent_emotion = max(emotions, key=emotions.get)
        result.append(schemas.DailyEmotionSummary(
            date=summary.date,
            prevalent_emotion=prevalent_emotion
        ))
    return result
