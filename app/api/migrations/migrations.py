import aiosqlite
from pathlib import Path


class DatabaseMigrator:
    def __init__(self, db_path: str = "schedule.sql"):
        self.db_path = Path(db_path)

    async def run_migrations(self):
        """Запуск всех необходимых миграций"""
        if not self.db_path.exists():
            print("🆕 Создаем новую базу данных...")
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.close()

        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Создаем основные таблицы если их нет
                await self._create_tables(conn)
                await self._add_new_columns(conn)
                print("✅ База данных инициализирована")
                return True

            except Exception as e:
                print(f"❌ Ошибка миграций: {e}")
                return False

    async def _create_tables(self, conn):
        """Создание всех таблиц"""
        # Таблица предметов (основная)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                total_hours INTEGER NOT NULL DEFAULT 0,
                remaining_hours INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(teacher, subject_name)
            )
        ''')

        # Таблица занятий
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL CHECK(day >= 0 AND day <= 6),
                time_slot INTEGER NOT NULL CHECK(time_slot >= 0 AND time_slot <= 3),
                teacher TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(day, time_slot)
            )
        ''')

        # Таблица фильтров
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS negative_filters (
                teacher TEXT PRIMARY KEY,
                restricted_days TEXT DEFAULT '[]',
                restricted_slots TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица преподавателей (новая)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица пользователей (новая)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица сохраненных расписаний (новая)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS saved_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payload TEXT NOT NULL
            )
        ''')

        await conn.commit()

    async def _add_new_columns(self, conn):
        """Добавляем новые колонки к существующим таблицам"""
        # Для таблицы subjects
        try:
            await conn.execute('ALTER TABLE subjects ADD COLUMN remaining_pairs INTEGER')
            print("✅ Добавлен remaining_pairs в subjects")
        except:
            pass  # Колонка уже существует

        try:
            await conn.execute('ALTER TABLE subjects ADD COLUMN priority INTEGER DEFAULT 0')
            print("✅ Добавлен priority в subjects")
        except:
            pass

        try:
            await conn.execute('ALTER TABLE subjects ADD COLUMN max_per_day INTEGER DEFAULT 2')
            print("✅ Добавлен max_per_day в subjects")
        except:
            pass

        # Для таблицы lessons
        try:
            await conn.execute('ALTER TABLE lessons ADD COLUMN editable BOOLEAN DEFAULT 1')
            print("✅ Добавлен editable в lessons")
        except:
            pass

        # Обновляем remaining_pairs если они NULL
        await conn.execute('''
            UPDATE subjects SET remaining_pairs = remaining_hours / 2 
            WHERE remaining_pairs IS NULL
        ''')

        await conn.commit()


# Глобальный экземпляр
migrator = DatabaseMigrator()