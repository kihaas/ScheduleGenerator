from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
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


@router.post("/generate")
async def generate_schedule_for_group(group_id: int = Query(1, description="ID группы")):
    """Сгенерировать расписание для указанной группы"""
    try:
        print(f"🔄 Начинаем генерацию расписания для группы {group_id}...")

        # Получаем предметы для группы
        subjects = await schedule_generator.get_subjects_for_group(group_id)
        print(f"📚 Найдено предметов в группе {group_id}: {len(subjects)}")

        # Получаем ГЛОБАЛЬНЫЕ ограничения
        from app.services.negative_filters_service import negative_filters_service
        negative_filters = await negative_filters_service.get_negative_filters()  # БЕЗ group_id
        print(f"🎯 Глобальных ограничений: {len(negative_filters)}")

        # Очищаем текущее расписание для этой группы
        await schedule_service.clear_schedule_for_group(group_id)

        # Генерируем расписание
        lessons = await schedule_generator.generate(subjects, negative_filters, group_id)

        print(f"✅ Расписание для группы {group_id} сгенерировано успешно")
        return {"message": f"Расписание для группы {group_id} сгенерировано", "lessons": len(lessons)}

    except Exception as e:
        print(f"❌ Ошибка генерации расписания: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-all")
async def clear_all_data(group_id: int = Query(1, description="ID группы")):
    """Очистить все данные группы (восстановить все часы)"""
    try:
        print(f"🧹 Очистка всех данных группы {group_id}")

        # 1. ВОССТАНАВЛИВАЕМ часы для всех уроков группы
        lessons = await database.fetch_all(
            'SELECT id, teacher, subject_name FROM lessons WHERE group_id = ?',
            (group_id,)
        )

        print(f"📊 Найдено уроков для очистки: {len(lessons)}")

        for lesson in lessons:
            lesson_id, teacher, subject_name = lesson

            # Находим предмет
            subject = await database.fetch_one(
                'SELECT id, remaining_hours, total_hours FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
                (teacher, subject_name, group_id)
            )

            if subject:
                subject_id, remaining_hours, total_hours = subject
                # Каждая пара = 2 часа, возвращаем их
                hours_to_restore = 2
                new_hours = min(remaining_hours + hours_to_restore, total_hours)
                new_pairs = new_hours // 2

                # Обновляем предмет
                await database.execute(
                    '''UPDATE subjects 
                       SET remaining_hours = ?,
                           remaining_pairs = ?
                       WHERE id = ?''',
                    (new_hours, new_pairs, subject_id)
                )
                print(f"✅ Восстановлено 2 часа для предмета {subject_id}")

        # 2. Удаляем все уроки группы
        deleted_count = await database.execute(
            'DELETE FROM lessons WHERE group_id = ?',
            (group_id,)
        )

        # 3. Полностью сбрасываем часы предметов к исходным значениям
        subjects = await database.fetch_all(
            'SELECT id, total_hours FROM subjects WHERE group_id = ?',
            (group_id,)
        )

        for subject in subjects:
            subject_id, total_hours = subject
            remaining_pairs = total_hours // 2

            await database.execute(
                '''UPDATE subjects 
                   SET remaining_hours = ?,
                       remaining_pairs = ?
                   WHERE id = ?''',
                (total_hours, remaining_pairs, subject_id)
            )

        print(f"✅ Удалено уроков: {deleted_count.rowcount}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": f"Все данные группы {group_id} очищены"}
        )

    except Exception as e:
        print(f"❌ Ошибка очистки данных: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки данных: {str(e)}")



