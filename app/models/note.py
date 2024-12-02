from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
import pytz

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # emotion counts
    happy_count = Column(Integer, default=0)
    calm_count = Column(Integer, default=0)
    sad_count = Column(Integer, default=0)
    upset_count = Column(Integer, default=0)

    user = relationship("User", back_populates="notes")
