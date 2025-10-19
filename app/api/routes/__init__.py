from fastapi import APIRouter
from . import schedule, subjects, lessons, schedule_api, teachers, users, statistics

api_router = APIRouter()

api_router.include_router(schedule.router)
api_router.include_router(subjects.router)
api_router.include_router(lessons.router)
api_router.include_router(schedule_api.router)
api_router.include_router(teachers.router)
api_router.include_router(users.router)
api_router.include_router(statistics.router)