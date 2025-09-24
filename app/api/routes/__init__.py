from fastapi import APIRouter
from . import schedule, subjects

api_router = APIRouter()

# УБИРАЕМ префиксы! → теперь роуты будут доступны напрямую:
api_router.include_router(schedule.router)        # → /generate-schedule
api_router.include_router(subjects.router)
