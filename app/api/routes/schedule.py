from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from app.services.schedule_services import schedule_service

router = APIRouter()

@router.post("/generate-schedule")
async def generate_schedule_route(request: Request):
    try:
        await schedule_service.generate_schedule()
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/remove-lesson")
async def remove_lesson(day: int = Form(...), time_slot: int = Form(...)):
    try:
        success = await schedule_service.remove_lesson(day, time_slot)
        if not success:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

