#!/usr/bin/env python3
import asyncio
from app.db.database import database


async def check_ids():
    """Проверить существующие ID в базе"""
    await database.init_db()

    print("📊 Проверка ID в базе данных:")

    # Преподаватели
    teachers = await database.fetch_all("SELECT id, name FROM teachers ORDER BY id")
    print(f"\n👨‍🏫 Преподаватели ({len(teachers)}):")
    for teacher in teachers:
        print(f"  ID {teacher[0]}: {teacher[1]}")

    # Предметы
    subjects = await database.fetch_all("SELECT id, teacher, subject_name FROM subjects ORDER BY id")
    print(f"\n📚 Предметы ({len(subjects)}):")
    for subject in subjects:
        print(f"  ID {subject[0]}: {subject[1]} - {subject[2]}")

    # Уроки
    lessons = await database.fetch_all("SELECT id, day, time_slot, teacher, subject_name FROM lessons ORDER BY id")
    print(f"\n📅 Уроки ({len(lessons)}):")
    for lesson in lessons:
        print(f"  ID {lesson[0]}: День {lesson[1]}, Пара {lesson[2]}, {lesson[3]} - {lesson[4]}")


if __name__ == "__main__":
    asyncio.run(check_ids())