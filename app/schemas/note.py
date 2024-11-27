from datetime import datetime, date
from pydantic import BaseModel
from typing import List, Dict

class NoteBase(BaseModel):
    text: str

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class NoteInDBBase(NoteBase):
    id: int
    created_at: datetime
    user_id: int

    # New emotion count fields
    happy_count: int
    calm_count: int
    sad_count: int
    upset_count: int

    class Config:
        orm_mode = True

class Note(NoteInDBBase):
    pass

class DailyAnalysis(BaseModel):
    date: date
    total_counts: Dict[str, int]
    notes: List[Note]

    class Config:
        orm_mode = True

class DailyEmotionSummary(BaseModel):
    date: date
    prevalent_emotion: str
