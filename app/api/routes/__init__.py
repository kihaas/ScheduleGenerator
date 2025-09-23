from fastapi import APIRouter
from . import schedule, subjects

api_router = APIRouter()
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["subjects"])