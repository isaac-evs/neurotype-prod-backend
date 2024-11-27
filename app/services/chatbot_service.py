import os
import openai
from datetime import date, timedelta

from app.services import note_service
from sqlalchemy.orm import Session

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_chatbot_response(user_message: str, current_user: User, db: Session) -> str:
    # Fetch notes for the current week
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    notes = note_service.get_notes_by_user_and_date(
        db, user_id=current_user.id, start_date=start_of_week, end_date=end_of_week
    )

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
    prompt = (
        f"You are a mental health assistant.\n"
        f"The user's prevalent emotion this week has been {prevalent_emotion}.\n"
        f"User: {user_message}\n"
        f"Assistant:"
    )

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=["\n", "User:", "Assistant:"],
        temperature=0.7,
    )
    answer = response.choices[0].text.strip()
    return answer
