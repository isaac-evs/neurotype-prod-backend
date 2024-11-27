from fastapi import APIRouter
from app.api.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router, tags=["users"])
