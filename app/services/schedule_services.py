from app.db.database import database
from app.db.models import Lesson
from typing import List, Optional
from app.services.shedule_generator import schedule_generator
import json

from app.services.subject_services import subject_service


class ScheduleService:
    def __init__(self):
        self.generator = schedule_generator

    async def generate_schedule(self, group_id: int = 1) -> List[Lesson]:
        """Сгенерировать расписание для конкретной группы"""
        print(f"🔄 Начинаем генерацию расписания для группы {group_id}...")

        # Получаем предметы для конкретной группы
        subjects = await subject_service.get_all_subjects(group_id)
        print(f"📚 Найдено предметов в группе {group_id}: {len(subjects)}")

        if not subjects:
            print("❌ Нет предметов для генерации")
            return []

        # Получаем фильтры для группы
        negative_filters = await subject_service.get_negative_filters(group_id)
        print(f"🎯 Ограничений для группы {group_id}: {len(negative_filters)}")

        # Очищаем старые уроки группы (часы ВОССТАНАВЛИВАЮТСЯ в методе remove_lesson)
        current_lessons = await self.get_all_lessons(group_id)
        for lesson in current_lessons:
            await self.remove_lesson(lesson.day, lesson.time_slot, group_id)

        # Генерируем расписание
        lessons = await self.generator.generate(subjects, negative_filters, group_id)

        # Сохраняем уроки БЕЗ обновления часов (часы уже учтены в генераторе)
        for lesson in lessons:
            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable, group_id) VALUES (?, ?, ?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name, int(lesson.editable), group_id)
            )

        print(f"✅ Сгенерировано уроков для группы {group_id}: {len(lessons)}")

        return lessons

    async def get_all_lessons(self, group_id: int = 1) -> List[Lesson]:
        """Получить все уроки группы"""
        rows = await database.fetch_all(
            'SELECT id, day, time_slot, teacher, subject_name, editable FROM lessons WHERE group_id = ? ORDER BY day, time_slot',
            (group_id,)
        )
        return [
            Lesson(
                id=row[0],
                day=row[1],
                time_slot=row[2],
                teacher=row[3],
                subject_name=row[4],
                editable=bool(row[5])
            )
            for row in rows
        ]

    async def remove_lesson(self, day: int, time_slot: int, group_id: int = 1) -> bool:
        """Удалить урок"""
        # Получаем удаляемый урок
        lesson = await database.fetch_one(
            'SELECT teacher, subject_name FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
            (day, time_slot, group_id)
        )

        if not lesson:
            return False

        teacher, subject_name = lesson

        # Восстанавливаем часы предмета
        await database.execute(
            '''UPDATE subjects 
               SET remaining_hours = remaining_hours + 2, 
                   remaining_pairs = remaining_pairs + 1 
               WHERE teacher = ? AND subject_name = ? AND group_id = ?''',
            (teacher, subject_name, group_id)
        )

        # Удаляем урок
        result = await database.execute(
            'DELETE FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
            (day, time_slot, group_id)
        )

        return result.rowcount > 0

    async def update_lesson(self, day: int, time_slot: int, new_teacher: str, new_subject_name: str,
                            group_id: int = 1) -> bool:
        """Обновить урок с проверкой конфликтов между группами"""
        try:
            # 1. Проверяем что преподаватель не занят в это время В ДРУГИХ ГРУППАХ
            conflict = await database.fetch_one(
                'SELECT id FROM lessons WHERE teacher = ? AND day = ? AND time_slot = ? AND group_id != ?',
                (new_teacher, day, time_slot, group_id)
            )
            if conflict:
                print(f"🚫 Преподаватель {new_teacher} уже занят в это время в другой группе")
                return False

            # 2. Проверяем что в текущей группе есть такой предмет
            subject_exists = await database.fetch_one(
                'SELECT id FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ? AND remaining_pairs > 0',
                (new_teacher, new_subject_name, group_id)
            )
            if not subject_exists:
                print(f"🚫 Предмет {new_subject_name} у преподавателя {new_teacher} не найден или нет пар")
                return False

            # 3. Получаем старый урок (если есть) для восстановления часов
            old_lesson = await database.fetch_one(
                'SELECT teacher, subject_name FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
                (day, time_slot, group_id)
            )

            if old_lesson:
                old_teacher, old_subject_name = old_lesson
                # Восстанавливаем часы старого предмета
                await database.execute(
                    '''UPDATE subjects 
                       SET remaining_hours = remaining_hours + 2, 
                           remaining_pairs = remaining_pairs + 1 
                       WHERE teacher = ? AND subject_name = ? AND group_id = ?''',
                    (old_teacher, old_subject_name, group_id)
                )

            # 4. Обновляем урок
            result = await database.execute(
                'UPDATE lessons SET teacher = ?, subject_name = ? WHERE day = ? AND time_slot = ? AND group_id = ?',
                (new_teacher, new_subject_name, day, time_slot, group_id)
            )

            if result.rowcount > 0:
                # 5. Уменьшаем часы нового предмета
                await database.execute(
                    '''UPDATE subjects 
                       SET remaining_hours = remaining_hours - 2, 
                           remaining_pairs = remaining_pairs - 1 
                       WHERE teacher = ? AND subject_name = ? AND group_id = ?''',
                    (new_teacher, new_subject_name, group_id)
                )
                return True

            return False
        except Exception as e:
            print(f"❌ Ошибка обновления урока: {e}")
            return False

    async def get_statistics(self, group_id: int = 1):
        """Получить статистику для группы"""
        try:
            # Предметы группы
            subjects_count = await database.fetch_one(
                'SELECT COUNT(*) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            # Преподаватели, которые ведут предметы в этой группе (локально)
            teachers_count = await database.fetch_one(
                'SELECT COUNT(DISTINCT teacher) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            # Часы группы
            hours_data = await database.fetch_one(
                'SELECT SUM(total_hours), SUM(remaining_hours) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            # Пары группы
            pairs_data = await database.fetch_one(
                'SELECT COUNT(*) FROM lessons WHERE group_id = ?',
                (group_id,)
            )

            total_hours = hours_data[0] or 0
            remaining_hours = hours_data[1] or 0
            scheduled_pairs = pairs_data[0] or 0
            remaining_pairs = (remaining_hours // 2) if remaining_hours else 0

            print(
                f"📊 Статистика группы {group_id}: {subjects_count[0] or 0} предметов, {teachers_count[0] or 0} преподавателей, {scheduled_pairs} пар, {remaining_hours}ч осталось")

            return {
                "total_subjects": subjects_count[0] or 0,
                "total_teachers": teachers_count[0] or 0,  # Локальные преподаватели группы
                "total_hours": total_hours,
                "remaining_hours": remaining_hours,
                "scheduled_pairs": scheduled_pairs,
                "remaining_pairs": remaining_pairs
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики для группы {group_id}: {e}")
            return {
                "total_subjects": 0,
                "total_teachers": 0,
                "total_hours": 0,
                "remaining_hours": 0,
                "scheduled_pairs": 0,
                "remaining_pairs": 0
            }

    def get_week_days(self):
        return ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    def get_time_slots(self):
        return [
            {"start": "9:00", "end": "10:30"},
            {"start": "10:40", "end": "12:10"},
            {"start": "12:40", "end": "14:10"},
            {"start": "14:20", "end": "15:50"}
        ]


# Глобальный экземпляр
schedule_service = ScheduleService()