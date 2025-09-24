from typing import List, Dict
import random
from datetime import datetime
from app.db.database import database
from app.db.models import Lesson
from app.services.subject_services import subject_service


class ScheduleService:
    async def get_all_lessons(self) -> List[Lesson]:
        rows = await database.fetch_all(
            'SELECT id, day, time_slot, teacher, subject_name FROM lessons ORDER BY day, time_slot'
        )
        lessons = []
        for row in rows:
            lesson = Lesson(id=row[0], day=row[1], time_slot=row[2], teacher=row[3], subject_name=row[4])
            lesson.is_past = self._is_lesson_past(lesson.day, lesson.time_slot)
            lessons.append(lesson)
        return lessons

    async def save_lessons(self, lessons: List[Lesson]):
        # Очищаем старые занятия
        await database.execute('DELETE FROM lessons')

        # Сохраняем новые
        for lesson in lessons:
            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name) VALUES (?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name)
            )

    async def generate_schedule(self) -> List[Lesson]:
        subjects = await subject_service.get_all_subjects()
        negative_filters_raw = await subject_service.get_negative_filters()
        negative_filters = {
            teacher: nf.model_dump()
            for teacher, nf in negative_filters_raw.items()
        }

        if not subjects:
            return []

        lessons = []
        occupied_slots = set()  # Для отслеживания занятых слотов (day, time_slot)

        # Перемешиваем предметы для случайного распределения
        shuffled_subjects = subjects.copy()
        random.shuffle(shuffled_subjects)

        for subject in shuffled_subjects:
            hours_to_assign = subject.remaining_hours
            restrictions = negative_filters.get(subject.teacher, {})

            # Получаем доступные слоты для этого преподавателя
            available_slots = []
            for day in range(5):  # Пн-Пт
                if day in restrictions.get('restricted_days', []):
                    continue
                for time_slot in range(4):
                    if time_slot in restrictions.get('restricted_slots', []):
                        continue
                    if (day, time_slot) not in occupied_slots:
                        available_slots.append((day, time_slot))

            # Случайно перемешиваем доступные слоты
            random.shuffle(available_slots)

            # Распределяем часы
            for day, time_slot in available_slots:
                if hours_to_assign <= 0:
                    break

                lessons.append(Lesson(
                    day=day,
                    time_slot=time_slot,
                    teacher=subject.teacher,
                    subject_name=subject.subject_name
                ))
                occupied_slots.add((day, time_slot))
                hours_to_assign -= 2

        await self.save_lessons(lessons)
        await self._update_subjects_hours(lessons, subjects)
        return lessons

    async def remove_lesson(self, day: int, time_slot: int) -> bool:
        # Находим занятие
        lesson = await database.fetch_one(
            'SELECT teacher, subject_name FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        if not lesson:
            return False

        teacher, subject_name = lesson

        # Удаляем занятие
        await database.execute(
            'DELETE FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        # Возвращаем часы
        await subject_service.update_subject_hours(teacher, subject_name, 2)
        return True

    async def _update_subjects_hours(self, lessons: List[Lesson], subjects: List[Dict]):
        """Обновляет оставшиеся часы у предметов"""
        # Считаем распределенные часы по предметам
        assigned_hours = {}
        for lesson in lessons:
            key = (lesson.teacher, lesson.subject_name)
            assigned_hours[key] = assigned_hours.get(key, 0) + 2

        # Обновляем базу данных
        for subject in subjects:
            key = (subject.teacher, subject.subject_name)
            hours_assigned = assigned_hours.get(key, 0)
            new_remaining = max(0, subject.total_hours - hours_assigned)

            await database.execute(
                'UPDATE subjects SET remaining_hours = ? WHERE teacher = ? AND subject_name = ?',
                (new_remaining, subject.teacher, subject.subject_name)
            )

    def _is_lesson_past(self, lesson_day: int, time_slot: int) -> bool:
        now = datetime.now()
        current_day = now.weekday()

        if lesson_day < current_day:
            return True

        if lesson_day == current_day:
            end_times = [(10, 30), (12, 10), (14, 10), (15, 50)]
            if time_slot < len(end_times):
                end_hour, end_minute = end_times[time_slot]
                current_hour, current_minute = now.hour, now.minute
                return current_hour > end_hour or (current_hour == end_hour and current_minute > end_minute)

        return False

    def get_week_days(self):
        return ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    def get_time_slots(self):
        return [
            {'start': '9:00', 'end': '10:30'},
            {'start': '10:40', 'end': '12:10'},
            {'start': '12:40', 'end': '14:10'},
            {'start': '14:20', 'end': '15:50'}
        ]


schedule_service = ScheduleService()
