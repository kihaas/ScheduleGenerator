from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel

from app.services.teacher_service import teacher_service
from app.db.models import Teacher

router = APIRouter(tags=["teachers"])


class TeacherCreateRequest(BaseModel):
    name: str


class TeacherResponse(BaseModel):
    id: int
    name: str
    created_at: str


@router.post("/api/teachers", response_model=TeacherResponse)
async def create_teacher(request: TeacherCreateRequest):
    """Создать преподавателя"""
    try:
        teacher = await teacher_service.create_teacher(request.name)
        return TeacherResponse(
            id=teacher.id,
            name=teacher.name,
            created_at=teacher.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка создания преподавателя: {str(e)}")


@router.get("/api/teachers", response_model=List[TeacherResponse])
async def get_teachers():
    """Получить всех преподавателей"""
    try:
        teachers = await teacher_service.get_all_teachers()
        return [
            TeacherResponse(
                id=teacher.id,
                name=teacher.name,
                created_at=teacher.created_at.isoformat()
            )
            for teacher in teachers
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения преподавателей: {str(e)}")


@router.put("/api/teachers/{teacher_id}")
async def update_teacher(teacher_id: int, request: TeacherCreateRequest):
    """Обновить преподавателя"""
    try:
        teacher = await teacher_service.update_teacher(teacher_id, request.name)
        if not teacher:
            raise HTTPException(status_code=404, detail="Преподаватель не найден")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Преподаватель обновлен"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления преподавателя: {str(e)}")


@router.delete("/api/teachers/{teacher_id}")
async def delete_teacher(teacher_id: int):
    """Удалить преподавателя"""
    try:
        success = await teacher_service.delete_teacher(teacher_id)
        if not success:
            raise HTTPException(status_code=404, detail="Преподаватель не найден")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Преподаватель удален"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка удаления преподавателя: {str(e)}")