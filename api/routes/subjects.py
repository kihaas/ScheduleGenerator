from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel

from app.services.subject_services import subject_service

router = APIRouter(tags=["subjects"])


class SubjectResponse(BaseModel):
    id: int
    teacher: str
    subject_name: str
    total_hours: int
    remaining_hours: int
    remaining_pairs: int
    priority: int
    max_per_day: int


class SubjectCreateRequest(BaseModel):
    teacher: str
    subject_name: str
    hours: int
    priority: int = 0
    max_per_day: int = 2



@router.get("/api/subjects", response_model=List[SubjectResponse])
async def get_all_subjects():
    """Получить все уникальные предметы"""
    try:
        subjects = await subject_service.get_all_subjects()
        return [
            SubjectResponse(
                id=subject.id,
                teacher=subject.teacher,
                subject_name=subject.subject_name,
                total_hours=subject.total_hours,
                remaining_hours=subject.remaining_hours,
                remaining_pairs=subject.remaining_pairs,
                priority=subject.priority,
                max_per_day=subject.max_per_day
            )
            for subject in subjects
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения предметов: {str(e)}")


@router.post("/api/subjects")
async def create_subject_api(request: SubjectCreateRequest):
    """Создать предмет с проверкой уникальности"""
    try:
        # Проверяем существование предмета
        existing = await subject_service.get_subject_by_name(request.teacher, request.subject_name)
        if existing:
            return JSONResponse(
                status_code=409,
                content={"error": "Предмет с таким названием уже существует у этого преподавателя"}
            )

        # Создаем предмет
        subject = await subject_service.create_subject(
            request.teacher, request.subject_name, request.hours,
            request.priority, request.max_per_day
        )

        return JSONResponse(
            status_code=201,
            content={
                "id": subject.id,
                "teacher": subject.teacher,
                "subject_name": subject.subject_name,
                "total_hours": subject.total_hours,
                "remaining_hours": subject.remaining_hours,
                "remaining_pairs": subject.remaining_pairs,
                "priority": subject.priority,
                "max_per_day": subject.max_per_day
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания предмета: {str(e)}")


@router.delete("/api/subjects/{subject_id}")
async def delete_subject_api(subject_id: int):
    """Удалить предмет через API"""
    try:
        print(f"API: Удаление предмета {subject_id}")
        success = await subject_service.delete_subject(subject_id)
        if not success:
            raise HTTPException(status_code=404, detail="Предмет не найден")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Предмет удален"}
        )
    except Exception as e:
        print(f"API: Ошибка удаления предмета {subject_id}: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка удаления предмета: {str(e)}")

# Старый эндпоинт для совместимости (перенаправляем на новый)
@router.post("/remove-subject/{subject_id}")
async def remove_subject_old(subject_id: int):
    """Старый эндпоинт для обратной совместимости"""
    return await delete_subject_api(subject_id)

# Старый эндпоинт для совместимости
@router.post("/add-subject")
async def add_subject(
        teacher: str = Form(...),
        subject_name: str = Form(...),
        hours: int = Form(...),
        priority: int = Form(0),
        max_per_day: int = Form(2)
):
    try:
        await subject_service.create_subject(teacher, subject_name, hours, priority, max_per_day)
        return JSONResponse(status_code=303, headers={"Location": "/"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка добавления предмета: {str(e)}")


