from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

class PlanType(str, Enum):
    lite = "lite"
    plus = "plus"

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    plan: PlanType = PlanType.lite
    profile_photo_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[PlanType] = None

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
