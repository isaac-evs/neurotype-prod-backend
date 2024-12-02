# chatbot_service.py

import os
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.services import note_service
from app.models.user import User
import pytz  # Ensure pytz is imported

# Initialize the AsyncOpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_chatbot_response(user_message: str, current_user: User) -> str:
    # Define UTC timezone
    utc = pytz.UTC

    # Get current datetime in UTC
    now_utc = datetime.now(utc)
    today = now_utc.date()

    # Calculate start and end of the current week in UTC
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Convert dates to timezone-aware datetime objects
    start_of_week_datetime = datetime.combine(start_of_week, datetime.min.time()).replace(tzinfo=utc)
    end_of_week_datetime = datetime.combine(end_of_week, datetime.min.time()).replace(tzinfo=utc) + timedelta(days=1)

    db = SessionLocal()
    try:
        notes = note_service.get_notes_by_user_and_date(
            db,
            user_id=current_user.id,
            start_date=start_of_week_datetime,
            end_date=end_of_week_datetime
        )
    finally:
        db.close()

    # Summarize the emotions from the notes
    total_emotion_counts = {
        "happy": 0,
        "calm": 0,
        "sad": 0,
        "upset": 0,
    }

    for note in notes:
        total_emotion_counts["happy"] += note.happy_count
        total_emotion_counts["calm"] += note.calm_count
        total_emotion_counts["sad"] += note.sad_count
        total_emotion_counts["upset"] += note.upset_count

    prevalent_emotion = max(total_emotion_counts, key=total_emotion_counts.get)

    # Include the emotional summary in the prompt
    messages = [
        {"role": "system", "content": "You are a mental health assistant."},
        {"role": "assistant", "content": f"The user's prevalent emotion this week has been {prevalent_emotion}."},
        {"role": "user", "content": user_message},
    ]

    # Call OpenAI ChatCompletion API asynchronously
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7,
    )
    answer = response.choices[0].message.content.strip()
    return answer
