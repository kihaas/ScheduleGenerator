# app/services/schedule_services.py
from app.db.database import database
from app.db.models import Lesson
from typing import List
from app.services.shedule_generator import schedule_generator


class ScheduleService:
    def __init__(self):
        self.generator = schedule_generator

    async def generate_schedule(self, group_id: int = 1) -> List[Lesson]:
        """Просто используем главный генератор"""
        return await self.generator.generate_schedule(group_id)

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
        try:
            # Получаем удаляемый урок
            lesson = await database.fetch_one(
                'SELECT teacher, subject_name FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
                (day, time_slot, group_id)
            )

            if not lesson:
                return False

            teacher, subject_name = lesson

            # Восстанавливаем часы
            subject = await database.fetch_one(
                'SELECT id FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
                (teacher, subject_name, group_id)
            )

            if subject:
                subject_id = subject[0]
                # Восстанавливаем 2 часа
                await database.execute(
                    '''UPDATE subjects 
                       SET remaining_hours = remaining_hours + 2,
                           remaining_pairs = (remaining_hours + 2) / 2
                       WHERE id = ?''',
                    (subject_id,)
                )

            # Удаляем урок
            result = await database.execute(
                'DELETE FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
                (day, time_slot, group_id)
            )

            return result.rowcount > 0

        except Exception as e:
            print(f"❌ Ошибка удаления урока: {e}")
            return False

    # async def update_lesson(self, day: int, time_slot: int, new_teacher: str, new_subject_name: str,
    #                         group_id: int = 1) -> bool:
    #     """Обновить урок"""
    #     try:
    #         # Проверяем что преподаватель не занят в других группах
    #         conflict = await database.fetch_one(
    #             'SELECT id FROM lessons WHERE teacher = ? AND day = ? AND time_slot = ? AND group_id != ?',
    #             (new_teacher, day, time_slot, group_id)
    #         )
    #         if conflict:
    #             return False
    #
    #         # Проверяем что предмет существует
    #         new_subject = await database.fetch_one(
    #             'SELECT id, remaining_pairs FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
    #             (new_teacher, new_subject_name, group_id)
    #         )
    #         if not new_subject or new_subject[1] <= 0:
    #             return False
    #
    #         new_subject_id = new_subject[0]
    #
    #         # Получаем старый урок
    #         old_lesson = await database.fetch_one(
    #             'SELECT teacher, subject_name FROM lessons WHERE day = ? AND time_slot = ? AND group_id = ?',
    #             (day, time_slot, group_id)
    #         )
    #
    #         if old_lesson:
    #             old_teacher, old_subject_name = old_lesson
    #             # Восстанавливаем часы старого предмета
    #             old_subject = await database.fetch_one(
    #                 'SELECT id FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
    #                 (old_teacher, old_subject_name, group_id)
    #             )
    #             if old_subject:
    #                 old_subject_id = old_subject[0]
    #                 await database.execute(
    #                     '''UPDATE subjects
    #                        SET remaining_hours = remaining_hours + 2,
    #                            remaining_pairs = (remaining_hours + 2) / 2
    #                        WHERE id = ?''',
    #                     (old_subject_id,)
    #                 )
    #
    #         # Обновляем урок
    #         result = await database.execute(
    #             'UPDATE lessons SET teacher = ?, subject_name = ? WHERE day = ? AND time_slot = ? AND group_id = ?',
    #             (new_teacher, new_subject_name, day, time_slot, group_id)
    #         )
    #
    #         if result.rowcount == 0:
    #             # Если обновления не было, создаем новый
    #             result = await database.execute(
    #                 'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable, group_id) VALUES (?, ?, ?, ?, ?, ?)',
    #                 (day, time_slot, new_teacher, new_subject_name, 1, group_id)
    #             )
    #
    #         # Вычитаем часы нового предмета
    #         await database.execute(
    #             '''UPDATE subjects
    #                SET remaining_hours = remaining_hours - 2,
    #                    remaining_pairs = (remaining_hours - 2) / 2
    #                WHERE id = ?''',
    #             (new_subject_id,)
    #         )
    #         return True
    #
    #     except Exception as e:
    #         print(f"❌ Ошибка обновления урока: {e}")
    #         return False

    async def get_statistics(self, group_id: int = 1):
        """Получить статистику"""
        try:
            subjects_count = await database.fetch_one(
                'SELECT COUNT(*) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            teachers_count = await database.fetch_one(
                'SELECT COUNT(DISTINCT teacher) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            hours_data = await database.fetch_one(
                'SELECT SUM(total_hours), SUM(remaining_hours) FROM subjects WHERE group_id = ?',
                (group_id,)
            )

            pairs_data = await database.fetch_one(
                'SELECT COUNT(*) FROM lessons WHERE group_id = ?',
                (group_id,)
            )

            total_hours = hours_data[0] or 0
            remaining_hours = hours_data[1] or 0
            scheduled_pairs = pairs_data[0] or 0
            remaining_pairs = (remaining_hours // 2) if remaining_hours else 0

            return {
                "total_subjects": subjects_count[0] or 0,
                "total_teachers": teachers_count[0] or 0,
                "total_hours": total_hours,
                "remaining_hours": remaining_hours,
                "scheduled_pairs": scheduled_pairs,
                "remaining_pairs": remaining_pairs
            }
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {
                "total_subjects": 0,
                "total_teachers": 0,
                "total_hours": 0,
                "remaining_hours": 0,
                "scheduled_pairs": 0,
                "remaining_pairs": 0
            }


# Глобальный экземпляр
schedule_service = ScheduleService()