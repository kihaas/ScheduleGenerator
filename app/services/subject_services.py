from typing import List, Optional
from app.db.database import database
from app.db.models import Subject
from app.services.teacher_service import teacher_service


class SubjectService:
    async def get_all_subjects(self) -> List[Subject]:
        """Получить все предметы из таблицы subjects"""
        rows = await database.fetch_all(
            'SELECT id, teacher, subject_name, total_hours, remaining_hours, '
            'remaining_pairs, priority, max_per_day FROM subjects ORDER BY teacher, subject_name'
        )
        subjects = []
        for row in rows:
            subject = Subject(
                id=row[0],
                teacher=row[1],
                subject_name=row[2],
                total_hours=row[3],
                remaining_hours=row[4],
                remaining_pairs=row[5],
                priority=row[6],
                max_per_day=row[7]
            )
            subjects.append(subject)
        return subjects

    async def get_subject_by_name(self, teacher: str, subject_name: str) -> Optional[Subject]:
        """Найти предмет по преподавателю и названию"""
        row = await database.fetch_one(
            'SELECT id, teacher, subject_name, total_hours, remaining_hours, '
            'remaining_pairs, priority, max_per_day FROM subjects '
            'WHERE teacher = ? AND subject_name = ?',
            (teacher, subject_name)
        )

        if not row:
            return None

        return Subject(
            id=row[0],
            teacher=row[1],
            subject_name=row[2],
            total_hours=row[3],
            remaining_hours=row[4],
            remaining_pairs=row[5],
            priority=row[6],
            max_per_day=row[7]
        )

    async def create_subject(self, teacher: str, subject_name: str, hours: int,
                             priority: int = 0, max_per_day: int = 2) -> Subject:
        """Создать новый предмет"""
        # Создаем преподавателя если его нет
        await teacher_service.create_teacher(teacher)

        result = await database.execute(
            'INSERT INTO subjects (teacher, subject_name, total_hours, remaining_hours, '
            'remaining_pairs, priority, max_per_day) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (teacher, subject_name, hours, hours, hours // 2, priority, max_per_day)
        )

        # Получаем созданный предмет
        row = await database.fetch_one(
            'SELECT id, teacher, subject_name, total_hours, remaining_hours, '
            'remaining_pairs, priority, max_per_day FROM subjects WHERE id = ?',
            (result.lastrowid,)
        )

        return Subject(
            id=row[0],
            teacher=row[1],
            subject_name=row[2],
            total_hours=row[3],
            remaining_hours=row[4],
            remaining_pairs=row[5],
            priority=row[6],
            max_per_day=row[7]
        )

    async def delete_subject(self, subject_id: int) -> bool:
        """Удалить предмет и связанные уроки"""
        try:
            print(f"🔍 Поиск предмета с ID: {subject_id}")

            # Проверяем существование предмета
            subject_row = await database.fetch_one(
                'SELECT id, teacher, subject_name FROM subjects WHERE id = ?',
                (subject_id,)
            )

            if not subject_row:
                print(f"❌ Предмет с ID {subject_id} не найден")
                return False

            teacher, subject_name = subject_row[1], subject_row[2]
            print(f"📋 Найден предмет: {teacher} - {subject_name}")

            # Удаляем связанные уроки
            delete_lessons_result = await database.execute(
                'DELETE FROM lessons WHERE teacher = ? AND subject_name = ?',
                (teacher, subject_name)
            )
            print(f"🗑️ Удалено уроков: {delete_lessons_result.rowcount}")

            # Удаляем предмет
            delete_subject_result = await database.execute(
                'DELETE FROM subjects WHERE id = ?',
                (subject_id,)
            )

            success = delete_subject_result.rowcount > 0
            print(f"✅ Результат удаления предмета: {success}")

            return success

        except Exception as e:
            print(f"❌ Ошибка удаления предмета {subject_id}: {e}")
            return False


# Создаем экземпляр сервиса
subject_service = SubjectService()