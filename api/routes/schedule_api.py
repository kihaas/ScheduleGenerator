from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.services.schedule_services import schedule_service
from app.db.database import database

router = APIRouter(tags=["schedule-api"])


class GenerateScheduleResponse(BaseModel):
    success: bool
    lessons: List[Dict[str, Any]]
    message: str = "Расписание успешно сгенерировано"


class SaveScheduleRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    lessons: List[Dict[str, Any]] = Field(..., description="List of lessons")


class SavedScheduleResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    lesson_count: int


@router.post("/api/schedule/generate", response_model=GenerateScheduleResponse)
async def generate_schedule():
    """Сгенерировать новое расписание"""
    try:
        lessons = await schedule_service.generate_schedule()

        # Конвертируем в словари для JSON
        lessons_data = []
        for lesson in lessons:
            lesson_dict = {
                "day": lesson.day,
                "time_slot": lesson.time_slot,
                "teacher": lesson.teacher,
                "subject_name": lesson.subject_name,
                "editable": lesson.editable
            }
            if hasattr(lesson, 'id') and lesson.id:
                lesson_dict["id"] = lesson.id
            lessons_data.append(lesson_dict)

        return GenerateScheduleResponse(
            success=True,
            lessons=lessons_data,
            message=f"Сгенерировано {len(lessons)} пар"
        )

    except Exception as e:
        print(f"❌ Ошибка генерации расписания: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации расписания: {str(e)}"
        )


@router.post("/api/schedules/save")
async def save_schedule(request: SaveScheduleRequest):
    """Сохранить расписание"""
    try:
        # Создаем таблицу saved_schedules если не существует
        await database.execute('''
            CREATE TABLE IF NOT EXISTS saved_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payload TEXT NOT NULL
            )
        ''')

        # Сохраняем расписание
        payload = json.dumps({
            "lessons": request.lessons,
            "saved_at": datetime.now().isoformat()
        })

        result = await database.execute(
            'INSERT INTO saved_schedules (name, payload) VALUES (?, ?)',
            (request.name, payload)
        )

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Расписание сохранено",
                "schedule_id": result.lastrowid
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения расписания: {str(e)}"
        )


@router.get("/api/schedules", response_model=List[SavedScheduleResponse])
async def get_saved_schedules():
    """Получить список сохраненных расписаний"""
    try:
        rows = await database.fetch_all('''
            SELECT id, name, created_at, payload 
            FROM saved_schedules 
            ORDER BY created_at DESC
        ''')

        schedules = []
        for row in rows:
            id, name, created_at, payload = row
            lesson_count = 0

            try:
                payload_data = json.loads(payload)
                lesson_count = len(payload_data.get("lessons", []))
            except:
                pass

            schedules.append(SavedScheduleResponse(
                id=id,
                name=name,
                created_at=created_at,
                lesson_count=lesson_count
            ))

        return schedules

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения расписаний: {str(e)}"
        )


@router.get("/api/schedules/{schedule_id}")
async def get_schedule_detail(schedule_id: int):
    """Получить детали сохраненного расписания"""
    try:
        row = await database.fetch_one(
            'SELECT id, name, created_at, payload FROM saved_schedules WHERE id = ?',
            (schedule_id,)
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Расписание не найдено"
            )

        id, name, created_at, payload = row

        try:
            payload_data = json.loads(payload)
        except json.JSONDecodeError:
            payload_data = {"lessons": [], "error": "Invalid JSON"}

        return JSONResponse(
            status_code=200,
            content={
                "id": id,
                "name": name,
                "created_at": created_at,
                "lessons": payload_data.get("lessons", []),
                "saved_at": payload_data.get("saved_at")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения расписания: {str(e)}"
        )


@router.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """Удалить сохраненное расписание"""
    try:
        result = await database.execute(
            'DELETE FROM saved_schedules WHERE id = ?',
            (schedule_id,)
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Расписание не найдено"
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Расписание удалено"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления расписания: {str(e)}"
        )