# app/api/endpoints/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.api import deps
from app.schemas.dashboard import DashboardData, DailyEmotionData
from app.models.user import User
from app.services import note_service

router = APIRouter()

@router.get("/", response_model=DashboardData)
def get_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    total_notes = note_service.count_notes_by_user(db, user_id=current_user.id)

    # Calculate the start and end dates of the current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Convert dates to datetime
    start_of_week_datetime = datetime.combine(start_of_week, datetime.min.time())
    adjusted_end_of_week_datetime = datetime.combine(end_of_week, datetime.max.time()) + timedelta(seconds=1)

    # Fetch notes for the current week using the adjusted end date
    notes = note_service.get_notes_by_user_and_date(
        db,
        user_id=current_user.id,
        start_date=start_of_week_datetime,
        end_date=adjusted_end_of_week_datetime
    )

    # Initialize emotion counts
    total_emotion_counts = {
        "happy": 0,
        "calm": 0,
        "sad": 0,
        "upset": 0,
    }

    # Prepare daily emotion data
    daily_emotion_data = {}
    for i in range(7):
        date_i = start_of_week + timedelta(days=i)
        date_str = date_i.isoformat()
        daily_emotion_data[date_str] = {
            "happy": 0,
            "calm": 0,
            "sad": 0,
            "upset": 0,
        }

    # Aggregate emotion counts
    for note in notes:
        note_date_str = note.created_at.date().isoformat()
        if note_date_str in daily_emotion_data:
            daily_emotion_data[note_date_str]["happy"] += note.happy_count
            daily_emotion_data[note_date_str]["calm"] += note.calm_count
            daily_emotion_data[note_date_str]["sad"] += note.sad_count
            daily_emotion_data[note_date_str]["upset"] += note.upset_count

            total_emotion_counts["happy"] += note.happy_count
            total_emotion_counts["calm"] += note.calm_count
            total_emotion_counts["sad"] += note.sad_count
            total_emotion_counts["upset"] += note.upset_count

    # Prepare weekly emotion data for the graph
    weekly_emotion_data = []
    for date_str in sorted(daily_emotion_data.keys()):
        emotions = daily_emotion_data[date_str]
        weekly_emotion_data.append(DailyEmotionData(date=date_str, emotions=emotions))

    # Determine prevalent emotion of today
    today_str = today.isoformat()
    emotions_today = daily_emotion_data.get(today_str)
    if emotions_today:
        prevalent_emotion_today = max(emotions_today, key=emotions_today.get)
    else:
        prevalent_emotion_today = None

    return DashboardData(
        name=current_user.name,
        profile_photo_url=current_user.profile_photo_url,
        total_notes=total_notes,
        emotion_counts=total_emotion_counts,
        weekly_emotion_data=weekly_emotion_data,
        prevalent_emotion_today=prevalent_emotion_today,
        plan=current_user.plan,
    )
