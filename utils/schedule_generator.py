import random
from collections import defaultdict
from typing import List, Dict, Set, Tuple
from datetime import datetime

from app.db import database
from app.db.models import Subject, Lesson, NegativeFilter
from app.services.subject_services import subject_service


async def generate_schedule(self) -> List[Lesson]:
    subjects = await subject_service.get_all_subjects()  # предполагаем, что Subject теперь содержит remaining_pairs и optional priority/max_per_day
    negative_filters_raw = await subject_service.get_negative_filters()
    negative_filters = {
        teacher: nf.model_dump()
        for teacher, nf in negative_filters_raw.items()
    }

    if not subjects:
        return []

    # Подготовим mutable словарь предметов по ключу (teacher, subject_name)
    # и локальные копии remaining_pairs / priority / max_per_day
    subj_list = []
    for s in subjects:
        subj_list.append({
            'teacher': s.teacher,
            'subject_name': s.subject_name,
            # Если у тебя ещё не migrated to pairs — используй remaining_hours // 2
            'remaining_pairs': getattr(s, 'remaining_pairs', getattr(s, 'remaining_hours', 0) // 2),
            'priority': getattr(s, 'priority', None),
            'max_per_day': getattr(s, 'max_per_day', None)  # optional
        })

    # counters
    teacher_slot_booked = set()  # (teacher, day, time_slot)
    teacher_day_count = defaultdict(lambda: defaultdict(int))  # teacher_day_count[teacher][day] = number assigned that day
    subject_day_count = defaultdict(lambda: defaultdict(int))  # subject_day_count[(teacher,subject)][day]

    lessons = []

    all_slots = [(day, ts) for day in range(5) for ts in range(4)]  # Пн-Пт, 4 пары

    for day, time_slot in all_slots:
        # Собираем кандидатов
        candidates = []
        for s in subj_list:
            if s['remaining_pairs'] <= 0:
                continue

            # проверки negative filters
            nf = negative_filters.get(s['teacher'], {})
            if day in nf.get('restricted_days', []):
                continue
            if time_slot in nf.get('restricted_slots', []):
                continue

            # преподаватель не занят в этот слот
            if (s['teacher'], day, time_slot) in teacher_slot_booked:
                continue

            # лимит пар в день на преподавателя (если задан)
            if s['max_per_day'] is not None and teacher_day_count[s['teacher']][day] >= s['max_per_day']:
                continue

            # доп. ограничение: не делать >2 одинаковых пар одного предмета в один день (настраиваемо)
            if subject_day_count[(s['teacher'], s['subject_name'])][day] >= 2:
                continue

            candidates.append(s)

        if not candidates:
            # нет кандидатов для этого слота — пропустить (можно логировать)
            continue

        # веса: priority (если есть) иначе remaining_pairs
        weights = []
        for c in candidates:
            w = c['priority'] if (c.get('priority') is not None) else max(1, c['remaining_pairs'])
            weights.append(max(1, int(w)))

        chosen = random.choices(candidates, weights=weights, k=1)[0]

        # назначаем
        lessons.append(Lesson(
            day=day,
            time_slot=time_slot,
            teacher=chosen['teacher'],
            subject_name=chosen['subject_name']
        ))

        # пометим занятие
        teacher_slot_booked.add((chosen['teacher'], day, time_slot))
        teacher_day_count[chosen['teacher']][day] += 1
        subject_day_count[(chosen['teacher'], chosen['subject_name'])][day] += 1
        chosen['remaining_pairs'] -= 1

    # Сохраняем и обновляем часы
    await self.save_lessons(lessons)

    # Обновляем subjects в БД: запишем новые remaining_pairs
    for s in subj_list:
        # Записываем обратно в поле remaining_hours или remaining_pairs в БД
        # Предполагается, что subject_service поддерживает обновление remaining_pairs:
        await database.execute(
            'UPDATE subjects SET remaining_pairs = ? WHERE teacher = ? AND subject_name = ?',
            (s['remaining_pairs'], s['teacher'], s['subject_name'])
        )

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




def get_week_days():
    return ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']


def get_time_slots():
    return [
        {'start': '9:00', 'end': '10:30'},
        {'start': '10:40', 'end': '12:10'},
        {'start': '12:40', 'end': '14:10'},
        {'start': '14:20', 'end': '15:50'}
    ]


async def generate_schedule(self) -> List[Lesson]:
    max_attempts = 3
    for attempt in range(max_attempts):
        lessons = await self._generate_schedule_attempt()
        if self._is_schedule_complete(lessons):
            await self.save_lessons(lessons)
            await self._update_subjects_hours(lessons)
            return lessons

    # Если не удалось распределить все, сохраняем частичное расписание
    await self.save_lessons(lessons)
    await self._update_subjects_hours(lessons)
    return lessons


def _is_schedule_complete(self, lessons: List[Lesson]) -> bool:
    # Проверяем, что все часы распределены
    assigned_hours = {}
    for lesson in lessons:
        key = (lesson.teacher, lesson.subject_name)
        assigned_hours[key] = assigned_hours.get(key, 0) + 2

    subjects_hours = {(s.teacher, s.subject_name): s.remaining_hours for s in self.subjects}

    for key, required in subjects_hours.items():
        assigned = assigned_hours.get(key, 0)
        if assigned < required:
            return False
    return True
