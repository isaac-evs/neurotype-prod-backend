from fastapi import APIRouter
from app.api.endpoints import users, notes, dashboard, recommendations, data

api_router = APIRouter()
api_router.include_router(users.router, tags=["users"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
api_router.include_router(data.router, prefix="/data", tags=["data"])
