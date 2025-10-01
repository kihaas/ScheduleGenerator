import random
from typing import List, Dict, Set, Tuple
from datetime import datetime
from app.db.models import Subject, Lesson, NegativeFilter


def generate_schedule(subjects: List[Subject], negative_filters: List[NegativeFilter]) -> List[Lesson]:
    if not subjects:
        return []

    lessons = []
    subjects_copy = subjects.copy()
    negative_filters_dict = {f.teacher: f for f in negative_filters}

    # Create availability matrix
    teacher_availability = [[set() for _ in range(4)] for _ in range(7)]

    # Shuffle and sort subjects
    random.shuffle(subjects_copy)
    subjects_copy.sort(key=lambda x: (-x.remaining_hours, x.teacher))

    for subject in subjects_copy:
        hours_to_assign = subject.remaining_hours
        restrictions = negative_filters_dict.get(subject.teacher)

        while hours_to_assign >= 2:
            slot = find_available_slot(subject.teacher, teacher_availability, restrictions)
            if not slot:
                break

            day, time_slot = slot
            lessons.append(Lesson(
                day=day,
                time_slot=time_slot,
                teacher=subject.teacher,
                subject_name=subject.subject_name
            ))

            teacher_availability[day][time_slot].add(subject.teacher)
            hours_to_assign -= 2

    return lessons


def find_available_slot(teacher: str, teacher_availability: List[List[Set[str]]],
                        restrictions: NegativeFilter) -> Tuple[int, int]:
    available_slots = []

    for day in range(5):  # Weekdays only
        if restrictions and day in restrictions.restricted_days:
            continue

        for time_slot in range(4):
            if restrictions and time_slot in restrictions.restricted_slots:
                continue

            if teacher not in teacher_availability[day][time_slot]:
                available_slots.append((day, time_slot))

    return random.choice(available_slots) if available_slots else None


def check_past_lessons(lessons: List[Lesson]) -> List[Lesson]:
    now = datetime.now()
    current_day = now.weekday()
    current_hour = now.hour
    current_minute = now.minute

    for lesson in lessons:
        lesson.is_past = is_lesson_past(lesson.day, lesson.time_slot, current_day, current_hour, current_minute)

    return lessons


def is_lesson_past(lesson_day: int, time_slot: int, current_day: int, current_hour: int, current_minute: int) -> bool:
    if lesson_day < current_day:
        return True

    if lesson_day == current_day:
        end_times = [(10, 30), (12, 10), (14, 10), (15, 50)]
        if time_slot < len(end_times):
            end_hour, end_minute = end_times[time_slot]
            return current_hour > end_hour or (current_hour == end_hour and current_minute > end_minute)

    return False


def get_week_days():
    return ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


def get_time_slots():
    return [
        {'start': '9:00', 'end': '10:30'},
        {'start': '10:40', 'end': '12:10'},
        {'start': '12:40', 'end': '14:10'},
        {'start': '14:20', 'end': '15:50'}
    ]
