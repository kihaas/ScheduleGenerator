from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

from app.db.database import database
from app.api.routes import api_router
from app.services.schedule_services import schedule_service
from app.services.subject_services import subject_service
from app.services.teacher_service import teacher_service

app = FastAPI(
    title="Schedule Generator",
    description="Умный генератор учебного расписания",
    version="2.0.0",
    debug=True
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Инициализация приложения"""
    print("🔄 Инициализация базы данных...")
    await database.init_db()
    await run_migrations()
    print("✅ База данных готова")
    print("✅ Приложение готово")


@app.on_event("shutdown")
async def shutdown_event():
    """Завершение работы приложения"""
    print("🔴 Приложение завершает работу")


async def run_migrations():
    """Выполнение миграций"""
    try:
        # Миграция для новых полей
        await database.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        await database.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Добавляем недостающие колонки если их нет
        await database.execute('''
            CREATE TABLE IF NOT EXISTS saved_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payload TEXT NOT NULL
            )
        ''')

        # Создаем индексы для производительности
        await database.execute('''
            CREATE INDEX IF NOT EXISTS idx_lessons_day_time ON lessons(day, time_slot)
        ''')
        await database.execute('''
            CREATE INDEX IF NOT EXISTS idx_subjects_teacher ON subjects(teacher_name)
        ''')

        print("✅ Миграции выполнены успешно")

    except Exception as e:
        print(f"⚠️ Ошибка миграций: {e}")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    """Обработчик HTTP исключений"""
    if exc.status_code == 500:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Внутренняя ошибка сервера"
        })
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих исключений"""
    print(f"❌ Необработанная ошибка: {exc}")
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": f"Произошла ошибка: {str(exc)}"
    })


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница приложения"""
    try:
        subjects = [s.model_dump() for s in await subject_service.get_all_subjects()]
        lessons = [l.model_dump() for l in await schedule_service.get_all_lessons()]
        teachers = [t.model_dump() for t in await teacher_service.get_all_teachers()]
        negative_filters = {
            teacher: nf.model_dump()
            for teacher, nf in (await subject_service.get_negative_filters()).items()
        }

        # Создаем матрицу расписания для шаблона
        schedule_matrix = [[None for _ in range(4)] for _ in range(7)]
        for lesson in lessons:
            day = lesson['day']
            time_slot = lesson['time_slot']
            if 0 <= day < 7 and 0 <= time_slot < 4:
                schedule_matrix[day][time_slot] = lesson

        return templates.TemplateResponse("index.html", {
            "request": request,
            "subjects": subjects,
            "teachers": teachers,
            "negative_filters": negative_filters,
            "schedule_matrix": schedule_matrix,
            "week_days": schedule_service.get_week_days(),
            "time_slots": schedule_service.get_time_slots(),
            "total_days": 7,
            "total_time_slots": 4
        })

    except Exception as e:
        print(f"❌ Ошибка загрузки главной страницы: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки данных: {str(e)}"
        })


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "ok",
        "message": "Service is running",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)