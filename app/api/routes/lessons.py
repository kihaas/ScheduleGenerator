from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.services.schedule_services import schedule_service

router = APIRouter(tags=["lessons"])


class UpdateLessonRequest(BaseModel):
    day: int
    time_slot: int
    new_teacher: str
    new_subject_name: str


@router.post("/remove-lesson")
async def remove_lesson_old(day: int = Form(...), time_slot: int = Form(...)):
    """Старый эндпоинт для обратной совместимости"""
    try:
        success = await schedule_service.remove_lesson(day, time_slot)
        if not success:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/lessons")
async def remove_lesson_api(
        day: int = Query(..., ge=0, le=6, description="Day of week (0-6)"),
        time_slot: int = Query(..., ge=0, le=3, description="Time slot (0-3)")
):
    """Удалить урок по дню и временному слоту"""
    try:
        print(f"🗑️ Удаление урока: день {day}, слот {time_slot}")

        success = await schedule_service.remove_lesson(day, time_slot)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Урок не найден или не может быть удален"
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Урок успешно удален"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка удаления урока: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления урока: {str(e)}"
        )


@router.patch("/api/lessons")
async def update_lesson_api(request: UpdateLessonRequest):
    """Обновить урок (правильная версия с Pydantic моделью)"""
    try:
        print(
            f"🔄 Замена урока: день {request.day}, слот {request.time_slot}, новый препод {request.new_teacher}, новый предмет {request.new_subject_name}")

        # Базовая проверка
        if not request.new_teacher or not request.new_subject_name:
            raise HTTPException(status_code=400, detail="Заполните все поля")

        if len(request.new_teacher.strip()) < 1 or len(request.new_subject_name.strip()) < 1:
            raise HTTPException(status_code=400, detail="Поля не могут быть пустыми")

        success = await schedule_service.update_lesson(
            request.day,
            request.time_slot,
            request.new_teacher.strip(),
            request.new_subject_name.strip()
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Не удалось обновить урок (возможно, урок не редактируемый или не найден)"
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Урок успешно обновлен"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка обновления урока: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления урока: {str(e)}"
        )


@router.post("/update-lesson")
async def update_lesson_old(
        day: int = Form(...),
        time_slot: int = Form(...),
        teacher: str = Form(...),
        subject_name: str = Form(...)
):
    """Старый эндпоинт для обратной совместимости"""
    try:
        success = await schedule_service.update_lesson(day, time_slot, teacher, subject_name)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot update lesson - may be not editable or not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/api/lessons")
async def update_lesson_api(request: UpdateLessonRequest):
    """Обновить урок"""
    try:
        print("=" * 50)
        print("🔄 ПОЛУЧЕН ЗАПРОС НА ЗАМЕНУ УРОКА")
        print(f"📥 Данные запроса: {request}")
        print(f"📥 Day: {request.day} (type: {type(request.day)})")
        print(f"📥 Time slot: {request.time_slot} (type: {type(request.time_slot)})")
        print(f"📥 New teacher: '{request.new_teacher}'")
        print(f"📥 New subject: '{request.new_subject_name}'")

        # Базовая проверка
        if not request.new_teacher or not request.new_subject_name:
            print("❌ Валидация: не все поля заполнены")
            raise HTTPException(status_code=400, detail="Заполните все поля")

        if len(request.new_teacher.strip()) < 1 or len(request.new_subject_name.strip()) < 1:
            print("❌ Валидация: поля пустые после trim")
            raise HTTPException(status_code=400, detail="Поля не могут быть пустыми")

        print("✅ Валидация пройдена, вызываем schedule_service.update_lesson...")

        success = await schedule_service.update_lesson(
            request.day,
            request.time_slot,
            request.new_teacher.strip(),
            request.new_subject_name.strip()
        )

        print(f"📤 Результат update_lesson: {success}")

        if not success:
            print("❌ Сервис вернул False")
            raise HTTPException(
                status_code=400,
                detail="Не удалось обновить урок (возможно, урок не редактируемый или не найден)"
            )

        print("✅ Урок успешно обновлен!")
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Урок успешно обновлен"}
        )

    except HTTPException as he:
        print(f"❌ HTTPException: {he.detail}")
        raise he
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")
        import traceback
        print(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обновления урока: {str(e)}"
        )
    finally:
        print("=" * 50)
