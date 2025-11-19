from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.schedule_services import schedule_service

router = APIRouter(tags=["statistics"])


class StatisticsResponse(BaseModel):
    total_subjects: int
    total_teachers: int
    total_hours: int
    remaining_hours: int
    scheduled_pairs: int
    remaining_pairs: int


@router.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получить статистику"""
    try:
        stats = await schedule_service.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")