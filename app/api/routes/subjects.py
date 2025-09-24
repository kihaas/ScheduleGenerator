from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.services.subject_services import subject_service

router = APIRouter()

@router.post("/add-subject")
async def add_subject(
    request: Request,
    teacher: str = Form(...),
    subject_name: str = Form(...),
    hours: int = Form(...)
):
    try:
        await subject_service.create_subject(teacher, subject_name, hours)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка добавления предмета: {str(e)}")

@router.post("/remove-subject/{subject_id}")
async def remove_subject(subject_id: int):
    try:
        success = await subject_service.delete_subject(subject_id)
        if not success:
            raise HTTPException(status_code=404, detail="Предмет не найден")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка удаления предмета: {str(e)}")

@router.post("/add-negative-filter")
async def add_negative_filter(
    teacher: str = Form(...),
    restricted_days: list[int] = Form([]),
    restricted_slots: list[int] = Form([])
):
    try:
        await subject_service.save_negative_filter(teacher, restricted_days, restricted_slots)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения фильтра: {str(e)}")

@router.post("/remove-negative-filter/{teacher}")
async def remove_negative_filter(teacher: str):
    try:
        await subject_service.remove_negative_filter(teacher)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка удаления фильтра: {str(e)}")

@router.post("/clear-all")
async def clear_all():
    try:
        await subject_service.clear_all_data()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка очистки данных: {str(e)}")