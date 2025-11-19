from typing import List, Optional
from app.db.database import database
from app.db.models import Teacher


class TeacherService:
    async def get_all_teachers(self) -> List[Teacher]:
        """Получить всех преподавателей"""
        rows = await database.fetch_all(
            'SELECT id, name, created_at FROM teachers ORDER BY name'
        )
        return [
            Teacher(id=row[0], name=row[1], created_at=row[2])
            for row in rows
        ]

    async def create_teacher(self, name: str) -> Teacher:
        """Создать преподавателя"""
        # Проверяем существование
        existing = await database.fetch_one(
            'SELECT id, name, created_at FROM teachers WHERE name = ?',
            (name,)
        )

        if existing:
            return Teacher(id=existing[0], name=existing[1], created_at=existing[2])

        # Создаем нового
        result = await database.execute(
            'INSERT INTO teachers (name) VALUES (?)',
            (name,)
        )

        # Получаем созданного преподавателя
        row = await database.fetch_one(
            'SELECT id, name, created_at FROM teachers WHERE id = ?',
            (result.lastrowid,)
        )

        return Teacher(id=row[0], name=row[1], created_at=row[2])

    async def update_teacher(self, teacher_id: int, name: str) -> Optional[Teacher]:
        """Обновить преподавателя"""
        result = await database.execute(
            'UPDATE teachers SET name = ? WHERE id = ?',
            (name, teacher_id)
        )

        if result.rowcount == 0:
            return None

        row = await database.fetch_one(
            'SELECT id, name, created_at FROM teachers WHERE id = ?',
            (teacher_id,)
        )

        return Teacher(id=row[0], name=row[1], created_at=row[2])

    async def get_teacher_by_name(self, name: str) -> Optional[Teacher]:
        """Найти преподавателя по имени"""
        row = await database.fetch_one(
            'SELECT id, name, created_at FROM teachers WHERE name = ?',
            (name,)
        )

        if not row:
            return None

        return Teacher(id=row[0], name=row[1], created_at=row[2])

    async def delete_teacher(self, teacher_id: int) -> bool:
        """Удалить преподавателя со всеми связанными данными"""
        try:
            # Получаем имя преподавателя
            teacher_row = await database.fetch_one(
                'SELECT name FROM teachers WHERE id = ?',
                (teacher_id,)
            )
            if not teacher_row:
                return False

            teacher_name = teacher_row[0]

            # Удаляем связанные уроки
            await database.execute(
                'DELETE FROM lessons WHERE teacher = ?',
                (teacher_name,)
            )

            # Удаляем связанные предметы
            await database.execute(
                'DELETE FROM subjects WHERE teacher = ?',
                (teacher_name,)
            )

            # Удаляем фильтры
            await database.execute(
                'DELETE FROM negative_filters WHERE teacher = ?',
                (teacher_name,)
            )

            # Удаляем преподавателя
            result = await database.execute(
                'DELETE FROM teachers WHERE id = ?',
                (teacher_id,)
            )

            return result.rowcount > 0

        except Exception as e:
            print(f"Error deleting teacher {teacher_id}: {e}")
            return False

    async def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        """Получить преподавателя по ID"""
        row = await database.fetch_one(
            'SELECT id, name, created_at FROM teachers WHERE id = ?',
            (teacher_id,)
        )

        if not row:
            return None

        return Teacher(id=row[0], name=row[1], created_at=row[2])

    async def teacher_exists(self, teacher_id: int) -> bool:
        """Проверить существование преподавателя"""
        row = await database.fetch_one(
            'SELECT id FROM teachers WHERE id = ?',
            (teacher_id,)
        )
        return row is not None


teacher_service = TeacherService()