from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse

from app.db.database import database
from app.services.schedule_services import schedule_service
from app.services.shedule_generator import schedule_generator
from app.services.negative_filters_service import negative_filters_service

router = APIRouter(tags=["schedule"])

# app/api/routes/schedule.py
from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.responses import JSONResponse

from app.db import database
from app.services.schedule_services import schedule_service
from app.services.shedule_generator import schedule_generator
from app.services.negative_filters_service import negative_filters_service

router = APIRouter(tags=["schedule"])


@router.post("/generate-schedule")
async def generate_schedule_route(request: Request):
    """Сгенерировать расписание (старый метод для одной группы)"""
    try:
        await schedule_service.generate_schedule()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# app/api/routes/schedule.py - УДАЛИТЕ старый метод или замените его:
@router.post("/generate")
async def generate_schedule_for_group(group_id: int = Query(1, description="ID группы")):
    """Генерация расписания (перенаправление на API)"""
    try:
        # Просто перенаправляем на API версию
        from app.services.shedule_generator import schedule_generator
        lessons = await schedule_generator.generate_schedule(group_id)

        return {
            "message": f"Расписание для группы {group_id} сгенерировано",
            "lessons": len(lessons)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-all")
async def clear_all_data(group_id: int = Query(1, description="ID группы")):
    """Очистить все данные группы (восстановить все часы)"""
    try:
        print(f"🧹 Очистка всех данных группы {group_id}")

        # Используем прямой SQL подход
        import aiosqlite
        from pathlib import Path

        db_path = Path("schedule.sql")

        async with aiosqlite.connect(db_path) as conn:
            await conn.execute("PRAGMA foreign_keys = ON")

            # 1. Восстанавливаем часы для всех предметов группы
            await conn.execute(
                '''UPDATE subjects 
                   SET remaining_hours = total_hours,
                       remaining_pairs = total_hours / 2 
                   WHERE group_id = ?''',
                (group_id,)
            )

            # 2. Удаляем все уроки группы
            cursor = await conn.execute(
                'DELETE FROM lessons WHERE group_id = ?',
                (group_id,)
            )
            deleted_count = cursor.rowcount

            await conn.commit()

        print(f"✅ Очищено данных группы {group_id}: удалено {deleted_count} уроков")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": f"Все данные группы {group_id} очищены"}
        )

    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки данных: {str(e)}")

