from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
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


@router.post("/generate")
async def generate_schedule_for_group(group_id: int = Query(1, description="ID группы")):
    """Сгенерировать расписание для указанной группы"""
    try:
        print(f"🔄 Начинаем генерацию расписания для группы {group_id}...")

        # Получаем предметы для группы
        subjects = await schedule_generator.get_subjects_for_group(group_id)
        print(f"📚 Найдено предметов в группе {group_id}: {len(subjects)}")

        # Получаем ограничения для группы
        negative_filters = await negative_filters_service.get_negative_filters_for_group(group_id)
        print(f"🎯 Ограничений для группы {group_id}: {len(negative_filters)}")

        # Очищаем текущее расписание для этой группы
        await schedule_service.clear_schedule_for_group(group_id)

        # Генерируем расписание
        lessons = await schedule_generator.generate(subjects, negative_filters, group_id)

        print(f"✅ Расписание для группы {group_id} сгенерировано успешно")
        return {"message": f"Расписание для группы {group_id} сгенерировано", "lessons": len(lessons)}

    except Exception as e:
        print(f"❌ Ошибка генерации расписания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-lesson")
async def remove_lesson(day: int = Form(...), time_slot: int = Form(...)):
    try:
        success = await schedule_service.remove_lesson(day, time_slot)
        if not success:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))