from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import database
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
async def get_statistics(group_id: int = Query(1, description="ID группы")):  # ДОБАВЬТЕ ПАРАМЕТР
    """Получить статистику"""
    try:
        stats = await schedule_service.get_statistics(group_id)  # ПЕРЕДАЙТЕ group_id
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


@router.post("/api/statistics/recalculate")
async def recalculate_statistics(group_id: int = Query(1, description="ID группы")):
    """Пересчитать статистику часов для группы"""
    try:
        # Пересчитываем оставшиеся часы на основе запланированных пар
        lessons = await database.fetch_all(
            'SELECT teacher, subject_name, COUNT(*) as count FROM lessons WHERE group_id = ? GROUP BY teacher, subject_name',
            (group_id,)
        )

        # Сбрасываем все часы к исходным значениям
        await database.execute(
            '''UPDATE subjects 
               SET remaining_hours = total_hours,
                   remaining_pairs = total_hours / 2 
               WHERE group_id = ?''',
            (group_id,)
        )

        # Вычитаем часы для запланированных пар
        for lesson in lessons:
            teacher, subject_name, count = lesson
            hours_to_subtract = count * 2

            result = await database.execute(
                '''UPDATE subjects 
                   SET remaining_hours = remaining_hours - ?, 
                       remaining_pairs = remaining_pairs - ? 
                   WHERE teacher = ? AND subject_name = ? AND group_id = ?''',
                (hours_to_subtract, count, teacher, subject_name, group_id)
            )

            if result.rowcount == 0:
                print(f"⚠️ Предмет не найден: {teacher} - {subject_name} в группе {group_id}")

        # Получаем обновленную статистику
        stats = await schedule_service.get_statistics(group_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Статистика для группы {group_id} пересчитана",
                "statistics": stats
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка пересчета статистики: {str(e)}")

