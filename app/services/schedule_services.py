from typing import List, Dict, Tuple
import random
from datetime import datetime
from app.db.database import database
from app.db.models import Lesson, Subject
from app.services.subject_services import subject_service
from app.services.teacher_service import teacher_service


class ScheduleService:
    async def get_all_lessons(self) -> List[Lesson]:
        """Получить все уроки"""
        rows = await database.fetch_all(
            'SELECT id, day, time_slot, teacher, subject_name, editable FROM lessons ORDER BY day, time_slot'
        )
        lessons = []
        for row in rows:
            # Автоматически создаем преподавателя если его нет
            teacher_name = row[3]
            if teacher_name:
                await teacher_service.create_teacher(teacher_name)

            lesson = Lesson(
                id=row[0],
                day=row[1],
                time_slot=row[2],
                teacher=teacher_name,
                subject_name=row[4],
                editable=bool(row[5]) if row[5] is not None else True
            )
            lessons.append(lesson)
        return lessons

    async def save_lessons(self, lessons: List[Lesson]):
        """Сохранить уроки"""
        await database.execute('DELETE FROM lessons')

        for lesson in lessons:
            # Создаем преподавателя если его нет
            if lesson.teacher:
                await teacher_service.create_teacher(lesson.teacher)

            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable) VALUES (?, ?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name, int(lesson.editable))
            )

    async def generate_schedule(self) -> List[Lesson]:
        """Генерация расписания с учетом приоритетов и ограничений"""
        subjects = await subject_service.get_all_subjects()
        negative_filters_raw = await subject_service.get_negative_filters()
        negative_filters = {
            teacher: nf.model_dump()
            for teacher, nf in negative_filters_raw.items()
        }

        if not subjects:
            return []

        # Инициализация структур для отслеживания
        subject_state = {}
        daily_teacher_count = {}
        daily_subject_count = {}

        for subject in subjects:
            key = (subject.teacher, subject.subject_name)
            subject_state[key] = {
                'remaining_pairs': subject.remaining_pairs,
                'priority': subject.priority,
                'max_per_day': subject.max_per_day
            }
            daily_teacher_count[subject.teacher] = {day: 0 for day in range(5)}
            daily_subject_count[key] = {day: 0 for day in range(5)}

        lessons = []
        occupied_slots = set()

        # Slot-first алгоритм с приоритетами
        for day in range(5):
            for time_slot in range(4):
                candidates = []

                for subject in subjects:
                    teacher = subject.teacher
                    subject_key = (teacher, subject.subject_name)
                    state = subject_state[subject_key]

                    # Проверяем доступность
                    if not await self._is_subject_available(
                            teacher, subject_key, state, day, time_slot,
                            daily_teacher_count, daily_subject_count, negative_filters, occupied_slots
                    ):
                        continue

                    # Вычисляем вес
                    weight = state['priority'] if state['priority'] > 0 else max(1, state['remaining_pairs'])

                    candidates.append({
                        'teacher': teacher,
                        'subject_name': subject.subject_name,
                        'weight': weight,
                        'subject_key': subject_key,
                        'state': state
                    })

                if candidates:
                    # Выбираем по весам
                    weights = [c['weight'] for c in candidates]
                    selected = random.choices(candidates, weights=weights, k=1)[0]

                    lesson = Lesson(
                        day=day,
                        time_slot=time_slot,
                        teacher=selected['teacher'],
                        subject_name=selected['subject_name'],
                        editable=True
                    )
                    lessons.append(lesson)
                    occupied_slots.add((day, time_slot))

                    # Обновляем состояние
                    teacher = selected['teacher']
                    subject_key = selected['subject_key']
                    subject_state[subject_key]['remaining_pairs'] -= 1
                    daily_teacher_count[teacher][day] += 1
                    daily_subject_count[subject_key][day] += 1

        await self.save_lessons(lessons)
        await self._update_subjects_pairs(lessons, subjects)
        return lessons

    async def _is_subject_available(self, teacher: str, subject_key: Tuple[str, str],
                                    state: Dict, day: int, time_slot: int,
                                    daily_teacher_count: Dict, daily_subject_count: Dict,
                                    negative_filters: Dict, occupied_slots: set) -> bool:
        """Проверить доступность предмета для слота"""
        if state['remaining_pairs'] <= 0:
            return False

        # Negative filters
        restrictions = negative_filters.get(teacher, {})
        if day in restrictions.get('restricted_days', []):
            return False
        if time_slot in restrictions.get('restricted_slots', []):
            return False

        # Макс пары в день для преподавателя
        if daily_teacher_count[teacher][day] >= 4:
            return False

        # Макс пары в день для предмета
        if daily_subject_count[subject_key][day] >= state['max_per_day']:
            return False

        return True

    async def remove_lesson(self, day: int, time_slot: int) -> bool:
        """Удалить урок и вернуть часы"""
        lesson = await database.fetch_one(
            'SELECT teacher, subject_name, editable FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        if not lesson:
            return False

        teacher, subject_name, editable = lesson
        if editable == 0:
            return False

        # Удаляем урок
        await database.execute(
            'DELETE FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        # Возвращаем пару (увеличиваем remaining_pairs)
        await database.execute('''
            UPDATE subjects 
            SET remaining_pairs = remaining_pairs + 1,
                remaining_hours = remaining_hours + 2
            WHERE teacher = ? AND subject_name = ?
        ''', (teacher, subject_name))

        return True

    async def update_lesson(self, day: int, time_slot: int, new_teacher: str, new_subject_name: str) -> bool:
        """Обновить урок"""
        current_lesson = await database.fetch_one(
            'SELECT teacher, subject_name, editable FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        if not current_lesson or not current_lesson[2]:
            return False

        old_teacher, old_subject_name, _ = current_lesson

        # Создаем нового преподавателя если нужно
        if new_teacher:
            await teacher_service.create_teacher(new_teacher)

        # Обновляем пары
        await subject_service.update_subject_pairs(old_teacher, old_subject_name, 1)
        await subject_service.update_subject_pairs(new_teacher, new_subject_name, -1)

        await database.execute(
            'UPDATE lessons SET teacher = ?, subject_name = ? WHERE day = ? AND time_slot = ?',
            (new_teacher, new_subject_name, day, time_slot)
        )

        return True

    async def _update_subjects_pairs(self, lessons: List[Lesson], subjects: List[Subject]):
        """Обновить оставшиеся пары у предметов"""
        assigned_pairs = {}
        for lesson in lessons:
            key = (lesson.teacher, lesson.subject_name)
            assigned_pairs[key] = assigned_pairs.get(key, 0) + 1

        for subject in subjects:
            key = (subject.teacher, subject.subject_name)
            assigned = assigned_pairs.get(key, 0)
            new_remaining = max(0, subject.remaining_pairs - assigned)

            if new_remaining != subject.remaining_pairs:
                await subject_service.update_subject_pairs(
                    subject.teacher, subject.subject_name,
                    new_remaining - subject.remaining_pairs
                )

    async def get_statistics(self) -> Dict[str, int]:
        """Получить статистику"""
        subjects = await subject_service.get_all_subjects()
        lessons = await self.get_all_lessons()
        teachers = await teacher_service.get_all_teachers()

        total_hours = sum(s.total_hours for s in subjects)
        remaining_hours = sum(s.remaining_hours for s in subjects)
        scheduled_pairs = len(lessons)
        remaining_pairs = sum(s.remaining_pairs for s in subjects)

        return {
            'total_subjects': len(subjects),
            'total_teachers': len(teachers),
            'total_hours': total_hours,
            'remaining_hours': remaining_hours,
            'scheduled_pairs': scheduled_pairs,
            'remaining_pairs': remaining_pairs
        }

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