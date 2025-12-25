from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
from app.db.database import database
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
    min_per_week: int
    max_per_week: int

class SubjectCreateRequest(BaseModel):
    teacher: str
    subject_name: str
    hours: int
    priority: int = 0
    max_per_day: int = 2
    min_per_week: int = 1
    max_per_week: int = 20


# app/api/routes/subjects.py
@router.get("/api/subjects", response_model=List[SubjectResponse])
async def get_all_subjects(group_id: int = Query(1, description="ID группы")):
    """Получить все уникальные предметы"""
    try:
        print(f"📚 API: Запрос предметов для группы {group_id}")

        subjects = await subject_service.get_all_subjects(group_id)

        print(f"✅ API: Отправлено {len(subjects)} предметов")

        # Формируем ответ
        response_data = [
            SubjectResponse(
                id=subject.id,
                teacher=subject.teacher,
                subject_name=subject.subject_name,
                total_hours=subject.total_hours,
                remaining_hours=subject.remaining_hours,
                remaining_pairs=subject.remaining_pairs,
                priority=subject.priority,
                max_per_day=subject.max_per_day,
                min_per_week=subject.min_per_week,
                max_per_week=subject.max_per_week
            )
            for subject in subjects
        ]

        return response_data

    except Exception as e:
        print(f"❌ API Ошибка получения предметов: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

        # ⭐ ВАЖНО: Возвращаем JSON с ошибкой, а не бросаем исключение
        # Это предотвратит возврат HTML страницы с ошибкой
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "error": "Ошибка загрузки предметов",
                "message": str(e),
                "subjects": []
            }
        )

# app/api/routes/subjects.py
@router.post("/api/subjects")
async def create_subject_api(request: SubjectCreateRequest, group_id: int = Query(1, description="ID группы")):
    """Создать предмет с недельными квотами"""
    try:
        print(f"🔄 Создание предмета: {request.teacher} - {request.subject_name} для группы {group_id}")

        # Проверяем существование предмета
        existing = await subject_service.get_subject_by_name(request.teacher, request.subject_name, group_id)
        if existing:
            print(f"❌ Предмет уже существует в группе {group_id}")
            return JSONResponse(
                status_code=409,
                content={
                    "error": f"Предмет '{request.subject_name}' уже существует у преподавателя {request.teacher} в этой группе"}
            )

        existing_row = await database.fetch_one(
            'SELECT id FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
            (request.teacher, request.subject_name, group_id)
        )

        if existing_row:
            return JSONResponse(
                status_code=409,
                content={"error": "Предмет с таким названием уже существует у этого преподавателя в этой группе"}
            )

        # Создаем предмет
        subject = await subject_service.create_subject(
            teacher=request.teacher,
            subject_name=request.subject_name,
            hours=request.hours,
            priority=request.priority,
            max_per_day=request.max_per_day,
            group_id=group_id,
            min_per_week=request.min_per_week,
            max_per_week=request.max_per_week
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
                "max_per_day": subject.max_per_day,
                "min_per_week": subject.min_per_week,
                "max_per_week": subject.max_per_week
            }
        )

    except ValueError as e:
        print(f"❌ ValueError: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        print(f"❌ Общая ошибка создания предмета: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания предмета: {str(e)}")



    #     # Проверяем что преподаватель существует (глобально)
    #     from app.services.teacher_service import teacher_service
    #     teacher_exists = await teacher_service.get_teacher_by_name(request.teacher)
    #     if not teacher_exists:
    #         print(f"❌ Преподаватель не найден: {request.teacher}")
    #         return JSONResponse(
    #             status_code=400,
    #             content={"error": f"Преподаватель '{request.teacher}' не существует. Сначала создайте преподавателя."}
    #         )
    #
    #     # Валидация недельных квот
    #     if request.min_per_week < 0:
    #         request.min_per_week = 0
    #     if request.max_per_week > 20:
    #         request.max_per_week = 20
    #     if request.min_per_week > request.max_per_week:
    #         request.min_per_week, request.max_per_week = request.max_per_week, request.min_per_week
    #
    #     if request.weeks_in_semester < 1:
    #         request.weeks_in_semester = 16
    #
    #     # Создаем предмет
    #     subject = await subject_service.create_subject(
    #         teacher=request.teacher,
    #         subject_name=request.subject_name,
    #         hours=request.hours,
    #         priority=request.priority,
    #         max_per_day=request.max_per_day,
    #         group_id=group_id,
    #         min_per_week=request.min_per_week,
    #         max_per_week=request.max_per_week,
    #     )
    #
    #     print(f"✅ Предмет создан: {subject.id}")
    #
    #     return JSONResponse(
    #         status_code=201,
    #         content={
    #             "id": subject.id,
    #             "teacher": subject.teacher,
    #             "subject_name": subject.subject_name,
    #             "total_hours": subject.total_hours,
    #             "remaining_hours": subject.remaining_hours,
    #             "remaining_pairs": subject.remaining_pairs,
    #             "priority": subject.priority,
    #             "max_per_day": subject.max_per_day,
    #             "min_per_week": subject.min_per_week,
    #             "max_per_week": subject.max_per_week,
    #         }
    #     )
    #
    # except ValueError as e:
    #     print(f"❌ ValueError: {e}")
    #     return JSONResponse(
    #         status_code=400,
    #         content={"error": str(e)}
    #     )
    # except Exception as e:
    #     print(f"❌ Общая ошибка создания предмета: {e}")
    #     import traceback
    #     print(f"❌ Traceback: {traceback.format_exc()}")
    #     return JSONResponse(
    #         status_code=500,
    #         content={"error": f"Внутренняя ошибка сервера: {str(e)}"}
    #     )



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
# В том же файле subjects.py, обновите старый эндпоинт:
@router.post("/add-subject")
async def add_subject(
        teacher: str = Form(...),
        subject_name: str = Form(...),
        hours: int = Form(...),
        priority: int = Form(0),
        max_per_day: int = Form(2),
        group_id: int = Form(1),  # Добавляем group_id
        min_per_week: int = Form(1),  # Добавляем новые параметры
        max_per_week: int = Form(20),
):
    try:
        await subject_service.create_subject(
            teacher=teacher,
            subject_name=subject_name,
            hours=hours,
            priority=priority,
            max_per_day=max_per_day,
            group_id=group_id,
            min_per_week=min_per_week,
            max_per_week=max_per_week,
        )
        return JSONResponse(status_code=303, headers={"Location": "/"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка добавления предмета: {str(e)}")

@router.get("/api/debug/subjects/{group_id}")
async def debug_subjects(group_id: int):
    """Отладочный эндпоинт для проверки предметов"""
    try:
        # Проверим какие предметы уже есть в группе
        rows = await database.fetch_all(
            'SELECT teacher, subject_name FROM subjects WHERE group_id = ?',
            (group_id,)
        )

        # Проверим какие преподаватели есть
        teachers = await database.fetch_all(
            'SELECT name FROM teachers'
        )

        return {
            "group_id": group_id,
            "existing_subjects": [{"teacher": r[0], "subject": r[1]} for r in rows],
            "available_teachers": [t[0] for t in teachers],
            "total_subjects": len(rows)
        }
    except Exception as e:
        return {"error": str(e)}
