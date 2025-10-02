# create_migration.py
from app.db.database import database


async def migrate_data():
    """Миграция данных из старой структуры в новую"""
    print("🔄 Запуск миграции данных...")

    try:
        # 1. Переносим уникальных преподавателей в teachers
        teachers = await database.fetch_all(
            'SELECT DISTINCT teacher FROM subjects WHERE teacher IS NOT NULL AND teacher != ""'
        )

        print(f"📋 Найдено {len(teachers)} уникальных преподавателей")

        for teacher_row in teachers:
            teacher_name = teacher_row[0]
            if teacher_name.strip():  # проверяем, что имя не пустое
                await database.execute(
                    'INSERT OR IGNORE INTO teachers (name) VALUES (?)',
                    (teacher_name.strip(),)
                )
                print(f"✅ Добавлен преподаватель: {teacher_name}")

        # 2. Обновляем teacher_id в subjects
        subjects = await database.fetch_all('SELECT id, teacher FROM subjects')
        print(f"📚 Обновление {len(subjects)} предметов...")

        updated_count = 0
        for subject in subjects:
            subject_id, teacher_name = subject
            if teacher_name.strip():
                teacher = await database.fetch_one(
                    'SELECT id FROM teachers WHERE name = ?',
                    (teacher_name.strip(),)
                )
                if teacher:
                    teacher_id = teacher[0]
                    await database.execute(
                        'UPDATE subjects SET teacher_id = ? WHERE id = ?',
                        (teacher_id, subject_id)
                    )
                    updated_count += 1
                    print(f"✅ Предмет {subject_id} привязан к преподавателю {teacher_id}")

        # 3. Добавляем базовые настройки
        default_settings = [
            ('week_start_day', '0'),  # 0=Понедельник
            ('pairs_per_day', '4'),  # 4 пары в день
            ('workdays', '0,1,2,3,4'),  # Пн-Пт
            ('generate_block_size', 'false'),  # стратегия генерации
            ('theme', 'light')  # тема по умолчанию
        ]

        for key, value in default_settings:
            await database.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
            print(f"⚙️  Добавлена настройка: {key} = {value}")

        print(f"🎉 Миграция завершена! Обновлено {updated_count} предметов")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        raise