from datetime import datetime
from models import Subject, Lesson
from typing import List


def generate_schedule(subjects: List[Subject]) -> List[Lesson]:
    lessons = []
    subjects_copy = [Subject(**subject.dict()) for subject in subjects]

    # Распределяем пары по дням и времени
    for day in range(5):  # Пн-Пт
        for time_slot in range(4):  # 4 пары в день
            # Ищем предмет с оставшимися часами
            available_subject = None
            for subject in subjects_copy:
                if subject.remaining_hours >= 2:
                    available_subject = subject
                    break

            if available_subject:
                lessons.append(Lesson(
                    day=day,
                    time_slot=time_slot,
                    teacher=available_subject.teacher,
                    subject_name=available_subject.subject_name
                ))
                available_subject.remaining_hours -= 2

    return lessons


def check_past_lessons(lessons: List[Lesson]) -> List[Lesson]:
    now = datetime.now()
    current_day = now.weekday()  # 0-6 (понедельник=0)
    current_hour = now.hour
    current_minute = now.minute

    updated_lessons = []

    for lesson in lessons:
        lesson_dict = lesson.dict()
        lesson_dict['is_past'] = is_lesson_past(lesson.day, lesson.time_slot, current_day, current_hour, current_minute)
        updated_lessons.append(Lesson(**lesson_dict))

    return updated_lessons


def is_lesson_past(lesson_day: int, time_slot: int, current_day: int, current_hour: int, current_minute: int) -> bool:
    if lesson_day < current_day:
        return True

    if lesson_day == current_day:
        # Временные интервалы пар
        end_times = [
            (10, 30),  # 9:00-10:30
            (12, 10),  # 10:40-12:10
            (14, 10),  # 12:40-14:10
            (15, 50)  # 14:20-15:50
        ]

        if time_slot < len(end_times):
            end_hour, end_minute = end_times[time_slot]
            if current_hour > end_hour or (current_hour == end_hour and current_minute > end_minute):
                return True

    return False


def get_week_days():
    return [
        'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница',
        'Суббота', 'Воскресенье'
    ]


def get_time_slots():
    return [
        {'start': '9:00', 'end': '10:30'},
        {'start': '10:40', 'end': '12:10'},
        {'start': '12:40', 'end': '14:10'},
        {'start': '14:20', 'end': '15:50'}
    ]