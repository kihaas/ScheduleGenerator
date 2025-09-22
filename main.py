from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Optional

from models import Subject, Lesson
from database import Database
from utils import generate_schedule, check_past_lessons, get_week_days, get_time_slots

app = FastAPI(title="Генератор расписания")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = Database()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    subjects = db.get_subjects()
    lessons = db.get_lessons()
    lessons_with_past = check_past_lessons(lessons)

    # Создаем матрицу расписания для отображения в таблице
    schedule_matrix = create_schedule_matrix(lessons_with_past)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "subjects": subjects,
            "schedule_matrix": schedule_matrix,
            "week_days": get_week_days(),
            "time_slots": get_time_slots(),
            "total_days": 7,
            "total_time_slots": 4
        }
    )


def create_schedule_matrix(lessons: List[Lesson]) -> List[List[Optional[Lesson]]]:
    # Создаем матрицу 7x4 (дни x пары)
    matrix = [[None for _ in range(4)] for _ in range(7)]

    for lesson in lessons:
        if 0 <= lesson.day < 7 and 0 <= lesson.time_slot < 4:
            matrix[lesson.day][lesson.time_slot] = lesson

    return matrix


@app.post("/add-subject")
async def add_subject(
        request: Request,
        teacher: str = Form(...),
        subject_name: str = Form(...),
        hours: int = Form(...)
):
    subjects = db.get_subjects()

    # Проверяем, существует ли уже такой предмет
    existing_index = -1
    for i, subject in enumerate(subjects):
        if subject.teacher == teacher and subject.subject_name == subject_name:
            existing_index = i
            break

    if existing_index >= 0:
        # Обновляем существующий предмет
        subjects[existing_index].total_hours += hours
        subjects[existing_index].remaining_hours += hours
    else:
        # Добавляем новый предмет
        new_subject = Subject(
            teacher=teacher,
            subject_name=subject_name,
            total_hours=hours,
            remaining_hours=hours
        )
        subjects.append(new_subject)

    db.save_subjects(subjects)
    return RedirectResponse(url="/", status_code=303)


@app.post("/remove-subject/{subject_id}")
async def remove_subject(subject_id: int):
    subjects = db.get_subjects()

    if 0 <= subject_id < len(subjects):
        subjects.pop(subject_id)
        db.save_subjects(subjects)

    return RedirectResponse(url="/", status_code=303)


@app.post("/generate-schedule")
async def generate_schedule_route():
    subjects = db.get_subjects()

    if not subjects:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы один предмет")

    lessons = generate_schedule(subjects)
    db.save_lessons(lessons)
    db.save_subjects(subjects)  # Сохраняем обновленные remaining_hours

    return RedirectResponse(url="/", status_code=303)


@app.post("/remove-lesson")
async def remove_lesson(day: int = Form(...), time_slot: int = Form(...)):
    lessons = db.get_lessons()
    subjects = db.get_subjects()

    # Находим удаляемое занятие
    lesson_to_remove = None
    new_lessons = []

    for lesson in lessons:
        if lesson.day == day and lesson.time_slot == time_slot:
            lesson_to_remove = lesson
        else:
            new_lessons.append(lesson)

    if lesson_to_remove:
        # Возвращаем 2 часа предмету
        for subject in subjects:
            if (subject.teacher == lesson_to_remove.teacher and
                    subject.subject_name == lesson_to_remove.subject_name):
                subject.remaining_hours += 2
                break

        db.save_lessons(new_lessons)
        db.save_subjects(subjects)

    return RedirectResponse(url="/", status_code=303)


@app.post("/clear-all")
async def clear_all():
    db.clear_all()
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)