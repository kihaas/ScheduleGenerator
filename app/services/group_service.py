from app.db.database import database
from app.db.models import StudyGroup, StudyGroupCreate
from typing import List, Optional
import json


class GroupService:
    async def get_all_groups(self) -> List[StudyGroup]:
        """Получить все группы"""
        rows = await database.fetch_all(
            'SELECT id, name, created_at FROM study_groups ORDER BY name'
        )
        return [
            StudyGroup(id=row[0], name=row[1], created_at=row[2])
            for row in rows
        ]

    async def create_group(self, name: str) -> StudyGroup:
        """Создать новую группу"""
        # Проверяем уникальность имени
        existing = await database.fetch_one(
            'SELECT id FROM study_groups WHERE name = ?',
            (name,)
        )
        if existing:
            raise ValueError(f"Группа с именем '{name}' уже существует")

        # Создаем группу
        result = await database.execute(
            'INSERT INTO study_groups (name) VALUES (?)',
            (name,)
        )

        group_id = result.lastrowid
        group = await database.fetch_one(
            'SELECT id, name, created_at FROM study_groups WHERE id = ?',
            (group_id,)
        )

        return StudyGroup(id=group[0], name=group[1], created_at=group[2])

    async def update_group(self, group_id: int, new_name: str) -> StudyGroup:
        """Переименовать группу"""
        # Проверяем существование группы
        existing = await database.fetch_one(
            'SELECT id FROM study_groups WHERE id = ?',
            (group_id,)
        )
        if not existing:
            raise ValueError("Группа не найдена")

        # Проверяем уникальность нового имени
        name_exists = await database.fetch_one(
            'SELECT id FROM study_groups WHERE name = ? AND id != ?',
            (new_name, group_id)
        )
        if name_exists:
            raise ValueError(f"Группа с именем '{new_name}' уже существует")

        # Обновляем имя
        await database.execute(
            'UPDATE study_groups SET name = ? WHERE id = ?',
            (new_name, group_id)
        )

        group = await database.fetch_one(
            'SELECT id, name, created_at FROM study_groups WHERE id = ?',
            (group_id,)
        )

        return StudyGroup(id=group[0], name=group[1], created_at=group[2])

    async def delete_group(self, group_id: int) -> bool:
        """Удалить группу и все её данные"""
        if group_id == 1:
            raise ValueError("Нельзя удалить основную группу")

        # Удаляем все данные группы
        tables = ['subjects', 'teachers', 'lessons', 'negative_filters']
        for table in tables:
            await database.execute(
                f'DELETE FROM {table} WHERE group_id = ?',
                (group_id,)
            )

        # Удаляем саму группу
        result = await database.execute(
            'DELETE FROM study_groups WHERE id = ?',
            (group_id,)
        )

        return result.rowcount > 0

    async def group_exists(self, group_id: int) -> bool:
        """Проверить существование группы"""
        row = await database.fetch_one(
            'SELECT id FROM study_groups WHERE id = ?',
            (group_id,)
        )
        return row is not None


# Глобальный экземпляр
group_service = GroupService()