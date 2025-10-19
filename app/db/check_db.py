#!/usr/bin/env python3
import asyncio
import aiosqlite


async def check_database():
    async with aiosqlite.connect("schedule.sql") as conn:
        # Проверяем таблицы
        tables = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_list = [row[0] for row in await tables.fetchall()]

        print("📊 Таблицы в базе данных:")
        for table in table_list:
            print(f"  - {table}")

        # Проверяем преподавателей
        teachers = await conn.execute("SELECT id, name FROM teachers")
        teacher_list = await teachers.fetchall()
        print(f"\n👨‍🏫 Преподаватели ({len(teacher_list)}):")
        for teacher in teacher_list:
            print(f"  - {teacher[0]}: {teacher[1]}")

        # Проверяем предметы
        subjects = await conn.execute("SELECT id, teacher, subject_name FROM subjects")
        subject_list = await subjects.fetchall()
        print(f"\n📚 Предметы ({len(subject_list)}):")
        for subject in subject_list:
            print(f"  - {subject[0]}: {subject[1]} - {subject[2]}")


if __name__ == "__main__":
    asyncio.run(check_database())
