from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, PlanType
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserCreate):
    hashed_password = get_password_hash(user_in.password)
    user = User(email=user_in.email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_plan(db: Session, user: User, plan: PlanType):
    user.plan = plan
    db.commit()
    db.refresh(user)
    return user

def update_user_profile(db: Session, user: User, update_data: dict):
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
