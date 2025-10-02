from typing import List, Optional, Dict
from app.db.database import database
from app.db.models import Subject, NegativeFilter
import json
from fastapi import HTTPException


class SubjectService:
    async def get_all_subjects(self) -> List[Subject]:
        """Получить все предметы с правильными ID"""
        rows = await database.fetch_all(
            'SELECT id, teacher, subject_name, total_hours, remaining_hours FROM subjects ORDER BY teacher, subject_name'
        )
        # ВАЖНО: создаем объекты Subject с ID
        return [
            Subject(
                id=row[0],  # ID из базы
                teacher=row[1],
                subject_name=row[2],
                total_hours=row[3],
                remaining_hours=row[4]
            ) for row in rows
        ]

    async def create_subject(self, teacher: str, subject_name: str, hours: int) -> Subject:
        """Создать или обновить предмет"""
        # Проверяем существование
        existing = await database.fetch_one(
            'SELECT id, total_hours, remaining_hours FROM subjects WHERE teacher = ? AND subject_name = ?',
            (teacher, subject_name)
        )

        if existing:
            # Обновляем существующий
            new_total = existing[1] + hours
            new_remaining = existing[2] + hours
            await database.execute(
                'UPDATE subjects SET total_hours = ?, remaining_hours = ? WHERE id = ?',
                (new_total, new_remaining, existing[0])
            )
            return Subject(
                id=existing[0],
                teacher=teacher,
                subject_name=subject_name,
                total_hours=new_total,
                remaining_hours=new_remaining
            )
        else:
            # Создаем новый
            result = await database.execute(
                'INSERT INTO subjects (teacher, subject_name, total_hours, remaining_hours) VALUES (?, ?, ?, ?)',
                (teacher, subject_name, hours, hours)
            )
            # Получаем ID созданной записи
            new_id = result.lastrowid
            return Subject(
                id=new_id,
                teacher=teacher,
                subject_name=subject_name,
                total_hours=hours,
                remaining_hours=hours
            )

    async def delete_subject(self, subject_id: int) -> bool:
        """Удалить предмет по ID"""
        result = await database.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
        return result.rowcount > 0

    async def get_negative_filters(self) -> Dict[str, NegativeFilter]:
        """Получить все негативные фильтры"""
        rows = await database.fetch_all('SELECT teacher, restricted_days, restricted_slots FROM negative_filters')
        filters = {}
        for row in rows:
            restricted_days = set(json.loads(row[1])) if row[1] else set()
            restricted_slots = set(json.loads(row[2])) if row[2] else set()
            filters[row[0]] = NegativeFilter(
                teacher=row[0],
                restricted_days=restricted_days,
                restricted_slots=restricted_slots
            )
        return filters

    async def save_negative_filter(self, teacher: str, restricted_days: list, restricted_slots: list):
        """Сохранить негативный фильтр с валидацией"""
        # ВАЖНО: Проверяем, что преподаватель существует
        subjects = await self.get_all_subjects()
        teachers = {s.teacher for s in subjects}

        if teacher not in teachers:
            raise HTTPException(
                status_code=400,
                detail=f"Преподаватель '{teacher}' не найден. Сначала добавьте предмет для этого преподавателя."
            )

        restricted_days_json = json.dumps([int(day) for day in restricted_days])
        restricted_slots_json = json.dumps([int(slot) for slot in restricted_slots])

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

    async def update_subject_hours(self, teacher: str, subject_name: str, hours_change: int):
        """Обновить количество часов у предмета"""
        await database.execute(
            'UPDATE subjects SET remaining_hours = remaining_hours + ? WHERE teacher = ? AND subject_name = ?',
            (hours_change, teacher, subject_name)
        )


subject_service = SubjectService()