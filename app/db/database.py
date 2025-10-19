import aiosqlite
from pathlib import Path
import os


class Database:
    def __init__(self, db_path: str = "schedule.sql"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._conn = None
        self._initialized = False

    async def _get_connection(self):
        """Создать новое соединение (вызывается для каждого запроса)"""
        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn

    async def execute(self, query: str, params: tuple = None):
        """Выполнить запрос"""
        conn = await self._get_connection()
        try:
            if params:
                result = await conn.execute(query, params)
            else:
                result = await conn.execute(query)
            await conn.commit()
            return result
        except Exception as e:
            await conn.rollback()
            raise e
        finally:
            await conn.close()

    async def fetch_all(self, query: str, params: tuple = None):
        """Получить все строки"""
        conn = await self._get_connection()
        try:
            if params:
                cursor = await conn.execute(query, params)
            else:
                cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
        except Exception as e:
            raise e
        finally:
            await conn.close()

    async def fetch_one(self, query: str, params: tuple = None):
        """Получить одну строку"""
        conn = await self._get_connection()
        try:
            if params:
                cursor = await conn.execute(query, params)
            else:
                cursor = await conn.execute(query)
            row = await cursor.fetchone()
            await cursor.close()
            return row
        except Exception as e:
            raise e
        finally:
            await conn.close()

    async def init_db(self):
        """Инициализация базы данных"""
        if self._initialized:
            return

        print("🔄 Инициализация базы данных...")

        try:
            # Создаем файл базы если не существует
            if not self.db_path.exists():
                print("🆕 Создаем новую базу данных...")
                conn = await self._get_connection()
                await conn.close()

            conn = await self._get_connection()

            # Проверяем существование таблиц
            tables = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in await tables.fetchall()]
            await tables.close()

            if 'subjects' not in existing_tables:
                print("📦 Создаем структуру базы данных...")

                # Таблица преподавателей
                await conn.execute('''
                    CREATE TABLE teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица предметов
                await conn.execute('''
                    CREATE TABLE subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher TEXT NOT NULL,
                        subject_name TEXT NOT NULL,
                        total_hours INTEGER NOT NULL DEFAULT 0,
                        remaining_hours INTEGER NOT NULL DEFAULT 0,
                        remaining_pairs INTEGER NOT NULL DEFAULT 0,
                        priority INTEGER DEFAULT 0,
                        max_per_day INTEGER DEFAULT 2,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(teacher, subject_name)
                    )
                ''')

                # Таблица занятий
                await conn.execute('''
                    CREATE TABLE lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        day INTEGER NOT NULL CHECK(day >= 0 AND day <= 6),
                        time_slot INTEGER NOT NULL CHECK(time_slot >= 0 AND time_slot <= 3),
                        teacher TEXT NOT NULL,
                        subject_name TEXT NOT NULL,
                        editable BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(day, time_slot)
                    )
                ''')

                # Таблица фильтров
                await conn.execute('''
                    CREATE TABLE negative_filters (
                        teacher TEXT PRIMARY KEY,
                        restricted_days TEXT DEFAULT '[]',
                        restricted_slots TEXT DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица пользователей
                await conn.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица сохраненных расписаний
                await conn.execute('''
                    CREATE TABLE saved_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payload TEXT NOT NULL
                    )
                ''')

                # Индексы для производительности
                await conn.execute('CREATE INDEX idx_subjects_teacher ON subjects(teacher)')
                await conn.execute('CREATE INDEX idx_lessons_day_time ON lessons(day, time_slot)')
                await conn.execute('CREATE INDEX idx_teachers_name ON teachers(name)')
                await conn.execute('CREATE INDEX idx_users_email ON users(email)')

                await conn.commit()
                print("✅ База данных создана с полной структурой")
            else:
                print("✅ База данных уже инициализирована")

            self._initialized = True

        except Exception as e:
            print(f"❌ Ошибка инициализации базы данных: {e}")
            raise
        finally:
            if 'conn' in locals():
                await conn.close()


# Глобальный экземпляр базы данных
database = Database()