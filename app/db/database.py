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
                print("📦 Создаем структуру базы данных с новой архитектурой...")

                # ТАБЛИЦА ГРУПП
                await conn.execute('''
                    CREATE TABLE study_groups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица преподавателей - БЕЗ group_id (ГЛОБАЛЬНЫЕ)
                await conn.execute('''
                    CREATE TABLE teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица предметов - С group_id (ЛОКАЛЬНЫЕ ДЛЯ ГРУППЫ)
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
                        group_id INTEGER DEFAULT 1,
                        UNIQUE(teacher, subject_name, group_id)
                    )
                ''')

                # Таблица занятий - С group_id (ЛОКАЛЬНЫЕ ДЛЯ ГРУППЫ)
                await conn.execute('''
                    CREATE TABLE lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        day INTEGER NOT NULL CHECK(day >= 0 AND day <= 6),
                        time_slot INTEGER NOT NULL CHECK(time_slot >= 0 AND time_slot <= 3),
                        teacher TEXT NOT NULL,
                        subject_name TEXT NOT NULL,
                        editable BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        group_id INTEGER DEFAULT 1,
                        UNIQUE(day, time_slot, group_id)
                    )
                ''')

                # Таблица фильтров - БЕЗ group_id (ГЛОБАЛЬНЫЕ)
                await conn.execute('''
                            CREATE TABLE negative_filters (
                                teacher TEXT PRIMARY KEY,
                                restricted_days TEXT DEFAULT '[]',
                                restricted_slots TEXT DEFAULT '[]',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')

                # Таблица сохраненных расписаний - С group_id
                await conn.execute('''
                    CREATE TABLE saved_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        payload TEXT NOT NULL,
                        group_id INTEGER DEFAULT 1
                    )
                ''')

                # Индексы для производительности
                await conn.execute('CREATE INDEX idx_subjects_teacher ON subjects(teacher)')
                await conn.execute('CREATE INDEX idx_lessons_day_time ON lessons(day, time_slot)')
                await conn.execute('CREATE INDEX idx_teachers_name ON teachers(name)')
                await conn.execute('CREATE INDEX idx_group_id_subjects ON subjects(group_id)')
                await conn.execute('CREATE INDEX idx_group_id_lessons ON lessons(group_id)')

                # Добавляем основную группу
                await conn.execute('INSERT INTO study_groups (id, name) VALUES (1, "Основная")')

                await conn.commit()
                print("✅ База данных создана с новой архитектурой (преподаватели глобальные)")
            else:
                print("✅ База данных уже инициализирована, применяем миграцию...")
                await self._migrate_to_new_architecture(conn)

            self._initialized = True

        except Exception as e:
            print(f"❌ Ошибка инициализации базы данных: {e}")
            raise
        finally:
            if 'conn' in locals():
                await conn.close()

    async def _migrate_to_new_architecture(self, conn):
        """Миграция на новую архитектуру (преподаватели глобальные)"""
        try:
            # 1. Убираем group_id из teachers если есть
            columns = await conn.execute("PRAGMA table_info(teachers)")
            column_names = [col[1] for col in await columns.fetchall()]

            if 'group_id' in column_names:
                print("🔄 Миграция: убираем group_id из teachers...")

                # Создаем временную таблицу без group_id
                await conn.execute('''
                    CREATE TABLE teachers_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Копируем уникальных преподавателей
                await conn.execute('''
                    INSERT OR IGNORE INTO teachers_new (id, name, created_at)
                    SELECT MIN(id), name, MIN(created_at) 
                    FROM teachers 
                    GROUP BY name
                ''')

                # Удаляем старую таблицу
                await conn.execute('DROP TABLE teachers')

                # Переименовываем новую таблицу
                await conn.execute('ALTER TABLE teachers_new RENAME TO teachers')

                print("✅ Преподаватели мигрированы в глобальную таблицу")

            # 2. Добавляем недостающие индексы
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_group_id_subjects ON subjects(group_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_group_id_lessons ON lessons(group_id)')

            print("✅ Миграция завершена")

        except Exception as e:
            print(f"⚠️ Ошибка миграции: {e}")


# Глобальный экземпляр базы данных
database = Database()