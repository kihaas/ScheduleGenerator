from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.db.database import database
import sys
from app.api.routes import api_router
from app.services.schedule_services import schedule_service
from app.services.subject_services import subject_service
from app.services.teacher_service import teacher_service
from pathlib import Path

app = FastAPI(
    title="Schedule Generator",
    description="Умный генератор учебного расписания",
    version="2.0.0",
    debug=True
)

# Mount static files and templates
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Инициализация базы данных...")
    try:
        await database.init_db()
        print("✅ База данных готова")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
    yield


app = FastAPI(
    title="Schedule Generator",
    description="Умный генератор учебного расписания",
    version="2.0.0",
    debug=True,
    lifespan=lifespan
)

# ✅ ИСПРАВЛЕННЫЕ ПУТИ - current_dir уже указывает на папку app
current_dir = Path(__file__).parent

# Пути относительно папки app
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(current_dir / "templates"))

app.include_router(api_router)


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

        # ИСПРАВЛЕННЫЙ КОД - используем правильный сервис для фильтров
        try:
            # Импортируем сервис фильтров
            from app.services.negative_filters_service import negative_filters_service
            negative_filters = await negative_filters_service.get_negative_filters()
            print(f"✅ Фильтры загружены: {len(negative_filters)} записей")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки фильтров: {e}")
            negative_filters = {}  # Пустой словарь вместо ошибки

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
            "week_days": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
            "time_slots": [
                {"start": "9:00", "end": "10:30"},
                {"start": "10:40", "end": "12:10"},
                {"start": "12:40", "end": "14:10"},
                {"start": "14:20", "end": "15:50"}
            ],
            "total_days": 7,
            "total_time_slots": 4
        })

    except Exception as e:
        print(f"❌ Ошибка загрузки главной страницы: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
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
    # Используем строку импорта вместо объекта app
    uvicorn.run("main:app", port=8000, reload=False)