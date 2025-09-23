from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db.database import database
from app.api import api_router
from app.services.schedule_services import schedule_service
from app.services.subject_services import subject_service

app = FastAPI(title="Schedule Generator", debug=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    print("Инициализация базы данных...")
    await database.init_db()
    print("База данных готова")


@app.on_event("shutdown")
async def shutdown_event():
    print("Приложение завершает работу")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 500:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Внутренняя ошибка сервера. Попробуйте перезагрузить страницу."
        })
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Необработанная ошибка: {exc}")
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": f"Произошла ошибка: {str(exc)}"
    })


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        subjects = await subject_service.get_all_subjects()
        lessons = await schedule_service.get_all_lessons()
        negative_filters = await subject_service.get_negative_filters()

        # Create schedule matrix for template
        schedule_matrix = [[None for _ in range(4)] for _ in range(7)]
        for lesson in lessons:
            if 0 <= lesson.day < 7 and 0 <= lesson.time_slot < 4:
                schedule_matrix[lesson.day][lesson.time_slot] = lesson

        return templates.TemplateResponse("index.html", {
            "request": request,
            "subjects": subjects,
            "negative_filters": negative_filters,
            "schedule_matrix": schedule_matrix,
            "week_days": schedule_service.get_week_days(),
            "time_slots": schedule_service.get_time_slots(),
            "total_days": 7,
            "total_time_slots": 4
        })

    except Exception as e:
        print(f"Ошибка в главной странице: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки данных: {str(e)}"
        })


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)