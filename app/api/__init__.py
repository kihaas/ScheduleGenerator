from fastapi import APIRouter
from app.api.routes import subjects, schedule

api_router = APIRouter()

api_router.include_router(subjects.router, prefix="/api", tags=["subjects"])
api_router.include_router(schedule.router, prefix="/api", tags=["schedule"])