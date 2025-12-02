from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse, RedirectResponse
from typing import List
from pydantic import BaseModel

from app.services.negative_filters_service import negative_filters_service

router = APIRouter(tags=["negative-filters"])


class NegativeFilterRequest(BaseModel):
    teacher: str
    restricted_days: List[int] = []
    restricted_slots: List[int] = []


@router.post("/api/negative-filters")
async def add_negative_filter_api(
        request: NegativeFilterRequest,
        group_id: int = Query(1, description="ID группы")
):
    """Добавить ограничения для преподавателя через JSON"""
    try:
        print(
            f"📨 Получен запрос: teacher={request.teacher}, days={request.restricted_days}, slots={request.restricted_slots}, group_id={group_id}")

        await negative_filters_service.save_negative_filter(
            request.teacher,
            request.restricted_days,
            request.restricted_slots,
            group_id
        )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Ограничения сохранены"}
        )
    except Exception as e:
        print(f"❌ Ошибка сохранения ограничений: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения ограничений: {str(e)}")


@router.get("/api/negative-filters")
async def get_negative_filters_api(group_id: int = Query(1, description="ID группы")):
    """Получить все ограничения"""
    try:
        filters = await negative_filters_service.get_negative_filters(group_id)
        return filters
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения ограничений: {str(e)}")


@router.delete("/api/negative-filters/{teacher}")
async def remove_negative_filter_api(
        teacher: str,
        group_id: int = Query(1, description="ID группы")
):
    """Удалить ограничения для преподавателя"""
    try:
        await negative_filters_service.remove_negative_filter(teacher, group_id)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Ограничения удалены"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка удаления ограничений: {str(e)}")


# Старый эндпоинт для обратной совместимости (HTML формы)
@router.post("/add-negative-filter")
async def add_negative_filter_old(
        teacher: str = Form(...),
        restricted_days: List[int] = Form([]),
        restricted_slots: List[int] = Form([])
):
    """Старый эндпоинт для обратной совместимости"""
    try:
        print(f"📨 Старый формат: teacher={teacher}, days={restricted_days}, slots={restricted_slots}")

        await negative_filters_service.save_negative_filter(teacher, restricted_days, restricted_slots)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения фильтра: {str(e)}")