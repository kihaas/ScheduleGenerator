from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.services.schedule_services import schedule_service

router = APIRouter(tags=["lessons"])


@router.post("/remove-lesson")
async def remove_lesson(day: int = Form(...), time_slot: int = Form(...)):
    try:
        success = await schedule_service.remove_lesson(day, time_slot)
        if not success:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/api/lessons")
async def update_lesson(
        day: int,
        time_slot: int,
        new_teacher: str,
        new_subject_name: str
):
    """Обновить урок (упрощенная валидация)"""
    try:
        # Базовая проверка
        if not new_teacher or not new_subject_name:
            raise HTTPException(status_code=400, detail="Заполните все поля")

        if len(new_teacher.strip()) < 1 or len(new_subject_name.strip()) < 1:
            raise HTTPException(status_code=400, detail="Поля не могут быть пустыми")

        success = await schedule_service.update_lesson(day, time_slot, new_teacher.strip(), new_subject_name.strip())
        if not success:
            raise HTTPException(status_code=400, detail="Не удалось обновить урок")

        return {"success": True, "message": "Урок успешно обновлен"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления урока: {str(e)}")

@router.post("/update-lesson")
async def update_lesson(
    day: int = Form(...),
    time_slot: int = Form(...),
    teacher: str = Form(...),
    subject_name: str = Form(...)
):
    try:
        success = await schedule_service.update_lesson(day, time_slot, teacher, subject_name)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot update lesson - may be not editable or not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))