from typing import List, Optional
from app.db.database import database
from app.db.models import Subject, NegativeFilter
from app.services.teacher_service import teacher_service
import json


class SubjectService:
    async def get_all_subjects(self) -> List[Subject]:
        """Получить все предметы"""
        rows = await database.fetch_all(
            'SELECT id, teacher, subject_name, total_hours, remaining_hours, remaining_pairs, priority, max_per_day FROM subjects ORDER BY teacher, subject_name'
        )
        subjects = []
        for row in rows:
            remaining_pairs = row[5] if row[5] is not None else row[4] // 2
            subject = Subject(
                id=row[0],
                teacher=row[1],
                subject_name=row[2],
                total_hours=row[3],
                remaining_hours=row[4],
                remaining_pairs=remaining_pairs,
                priority=row[6] or 0,
                max_per_day=row[7] or 2
            )
            subjects.append(subject)
        return subjects

    async def create_subject(self, teacher: str, subject_name: str, hours: int, priority: int = 0,
                             max_per_day: int = 2) -> Subject:
        """Создать предмет"""
        remaining_pairs = hours // 2

        # Создаем преподавателя если его нет
        if teacher:
            await teacher_service.create_teacher(teacher)

        existing = await database.fetch_one(
            'SELECT id, total_hours, remaining_hours, remaining_pairs FROM subjects WHERE teacher = ? AND subject_name = ?',
            (teacher, subject_name)
        )

        if existing:
            new_total = existing[1] + hours
            new_remaining = existing[2] + hours
            current_pairs = existing[3] if existing[3] is not None else existing[2] // 2
            new_remaining_pairs = current_pairs + remaining_pairs

            await database.execute(
                'UPDATE subjects SET total_hours = ?, remaining_hours = ?, remaining_pairs = ?, priority = ?, max_per_day = ? WHERE id = ?',
                (new_total, new_remaining, new_remaining_pairs, priority, max_per_day, existing[0])
            )

            return Subject(
                id=existing[0], teacher=teacher, subject_name=subject_name,
                total_hours=new_total, remaining_hours=new_remaining,
                remaining_pairs=new_remaining_pairs, priority=priority, max_per_day=max_per_day
            )
        else:
            result = await database.execute(
                'INSERT INTO subjects (teacher, subject_name, total_hours, remaining_hours, remaining_pairs, priority, max_per_day) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (teacher, subject_name, hours, hours, remaining_pairs, priority, max_per_day)
            )

            return Subject(
                id=result.lastrowid, teacher=teacher, subject_name=subject_name,
                total_hours=hours, remaining_hours=hours, remaining_pairs=remaining_pairs,
                priority=priority, max_per_day=max_per_day
            )

    async def delete_subject(self, subject_id: int) -> bool:
        """Удалить предмет и связанные уроки"""
        try:
            # Получаем данные предмета
            subject_row = await database.fetch_one(
                'SELECT teacher, subject_name FROM subjects WHERE id = ?',
                (subject_id,)
            )

            if not subject_row:
                return False

            teacher, subject_name = subject_row

            # Удаляем связанные уроки
            await database.execute(
                'DELETE FROM lessons WHERE teacher = ? AND subject_name = ?',
                (teacher, subject_name)
            )

            # Удаляем предмет
            result = await database.execute(
                'DELETE FROM subjects WHERE id = ?',
                (subject_id,)
            )

            return result.rowcount > 0

        except Exception as e:
            print(f"Error deleting subject {subject_id}: {e}")
            return False

    async def update_subject_pairs(self, teacher: str, subject_name: str, delta_pairs: int) -> None:
        """Обновить количество пар для предмета"""
        await database.execute(
            'UPDATE subjects SET remaining_pairs = remaining_pairs + ?, remaining_hours = remaining_hours + ? WHERE teacher = ? AND subject_name = ?',
            (delta_pairs, delta_pairs * 2, teacher, subject_name)
        )

    async def update_subject_priority(self, subject_id: int, priority: int) -> bool:
        """Обновить приоритет предмета"""
        result = await database.execute(
            'UPDATE subjects SET priority = ? WHERE id = ?',
            (priority, subject_id)
        )
        return result.rowcount > 0

    async def update_subject_max_per_day(self, subject_id: int, max_per_day: int) -> bool:
        """Обновить максимальное количество пар в день"""
        result = await database.execute(
            'UPDATE subjects SET max_per_day = ? WHERE id = ?',
            (max_per_day, subject_id)
        )
        return result.rowcount > 0

    async def get_negative_filters(self) -> dict:
        """Получить негативные фильтры"""
        rows = await database.fetch_all(
            'SELECT teacher, restricted_days, restricted_slots FROM negative_filters'
        )

        filters = {}
        for row in rows:
            teacher_name = row[0]
            restricted_days = set(json.loads(row[1])) if row[1] else set()
            restricted_slots = set(json.loads(row[2])) if row[2] else set()

            filters[teacher_name] = NegativeFilter(
                teacher=teacher_name,
                restricted_days=restricted_days,
                restricted_slots=restricted_slots
            )
        return filters

    async def save_negative_filter(self, teacher: str, restricted_days: list, restricted_slots: list):
        """Сохранить негативный фильтр"""
        if teacher:
            await teacher_service.create_teacher(teacher)

        restricted_days_json = json.dumps(restricted_days)
        restricted_slots_json = json.dumps(restricted_slots)

        await database.execute(
            'INSERT OR REPLACE INTO negative_filters (teacher, restricted_days, restricted_slots) VALUES (?, ?, ?)',
            (teacher, restricted_days_json, restricted_slots_json)
        )

    async def remove_negative_filter(self, teacher: str):
        """Удалить негативный фильтр"""
        await database.execute('DELETE FROM negative_filters WHERE teacher = ?', (teacher,))

    async def clear_all_data(self):
        """Очистить все данные"""
        await database.execute('DELETE FROM subjects')
        await database.execute('DELETE FROM lessons')
        await database.execute('DELETE FROM negative_filters')


subject_service = SubjectService()