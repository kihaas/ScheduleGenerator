from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    await database.init_db()  # ТОЛЬКО ЭТО - больше никаких миграций
    print("✅ База данных готова")
    print("✅ Приложение готово")


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
        # Пока загружаем только базовые данные без предметов
        teachers = []
        lessons = []
        negative_filters = {}

        try:
            teachers = [t.model_dump() for t in await teacher_service.get_all_teachers()]
            lessons = [l.model_dump() for l in await schedule_service.get_all_lessons()]
            negative_filters = {
                teacher: nf.model_dump()
                for teacher, nf in (await subject_service.get_negative_filters()).items()
            }
        except Exception as e:
            print(f"⚠️ Предупреждение при загрузке данных: {e}")

        # Создаем пустую матрицу расписания для шаблона
        schedule_matrix = [[None for _ in range(4)] for _ in range(7)]
        for lesson in lessons:
            day = lesson['day']
            time_slot = lesson['time_slot']
            if 0 <= day < 7 and 0 <= time_slot < 4:
                schedule_matrix[day][time_slot] = lesson

        return templates.TemplateResponse("index.html", {
            "request": request,
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