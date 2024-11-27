from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()

@router.get("/", summary="Get personalized recommendations")
def get_recommendations(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # To do: recommendation logic
    recommendations = ["Recommendation 1", "Recommendation 2"]
    return {"recommendations": recommendations}
