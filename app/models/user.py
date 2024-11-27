from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class PlanType(str, enum.Enum):
    lite = "lite"
    plus = "plus"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    name = Column(String, nullable=True)
    plan = Column(Enum(PlanType), default=PlanType.lite)
    profile_photo_url = Column(String, nullable=True)

    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
