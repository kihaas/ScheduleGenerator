from datetime import datetime
from models import Subject, Lesson, NegativeFilter
from typing import List, Dict, Set
import random
import copy


def generate_schedule(subjects: List[Subject], negative_filters: Dict[str, NegativeFilter]) -> List[Lesson]:
    lessons = []
    subjects_copy = copy.deepcopy(subjects)

    # Создаем матрицу занятости преподавателей
    teacher_availability = create_teacher_availability_matrix(negative_filters)

    # Случайно перемешиваем предметы для более равномерного распределения
    random.shuffle(subjects_copy)

    # Сортируем предметы по количеству оставшихся часов (сначала те, у кого больше)
    subjects_copy.sort(key=lambda x: x.remaining_hours, reverse=True)

    # Пытаемся распределить все часы
    for subject in subjects_copy:
        hours_to_assign = subject.remaining_hours

        while hours_to_assign >= 2:
            # Ищем доступный слот для этого преподавателя
            slot = find_available_slot(subject.teacher, teacher_availability, negative_filters)

            if slot:
                day, time_slot = slot
                lessons.append(Lesson(
                    day=day,
                    time_slot=time_slot,
                    teacher=subject.teacher,
                    subject_name=subject.subject_name
                ))
                teacher_availability[day][time_slot].add(subject.teacher)
                hours_to_assign -= 2
                subject.remaining_hours -= 2
            else:
                # Не можем найти подходящий слот, прерываем
                break

    return lessons


def create_teacher_availability_matrix(negative_filters: Dict[str, NegativeFilter]) -> List[List[Set[str]]]:
    # Создаем матрицу 7x4 (дни x пары) с множествами занятых преподавателей
    return [[set() for _ in range(4)] for _ in range(7)]


def find_available_slot(teacher: str, teacher_availability: List[List[Set[str]]],
                        negative_filters: Dict[str, NegativeFilter]) -> tuple:
    # Получаем ограничения для преподавателя
    restrictions = negative_filters.get(teacher, NegativeFilter(teacher=teacher))

    # Создаем список всех возможных слотов и перемешиваем его
    all_slots = [(day, time_slot) for day in range(5) for time_slot in range(4)]
    random.shuffle(all_slots)

    for day, time_slot in all_slots:
        # Проверяем ограничения
        if day in restrictions.restricted_days:
            continue
        if time_slot in restrictions.restricted_slots:
            continue

        # Проверяем, не занят ли слот другим преподавателем
        if teacher not in teacher_availability[day][time_slot]:
            return (day, time_slot)

    return None


def check_past_lessons(lessons: List[Lesson]) -> List[Lesson]:
    now = datetime.now()
    current_day = now.weekday()
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


def get_day_name(day_index: int) -> str:
    days = get_week_days()
    return days[day_index] if 0 <= day_index < len(days) else ""


def get_time_slot_name(time_slot: int) -> str:
    slots = get_time_slots()
    if 0 <= time_slot < len(slots):
        return f"{slots[time_slot]['start']}-{slots[time_slot]['end']}"
    return ""