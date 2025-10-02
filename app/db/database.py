import aiosqlite
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "schedule.db"):  # ← исправил название на schedule.db
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

    async def get_connection(self):
        """Создает новое соединение для каждого запроса"""
        conn = await aiosqlite.connect(self.db_path)
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn

    async def execute(self, query: str, params: tuple = None):
        """Упрощенный метод для выполнения запросов"""
        conn = await self.get_connection()
        try:
            if params:
                result = await conn.execute(query, params)
            else:
                result = await conn.execute(query)
            await conn.commit()
            return result
        finally:
            await conn.close()

    async def fetch_all(self, query: str, params: tuple = None):
        """Получить все строки"""
        conn = await self.get_connection()
        try:
            if params:
                cursor = await conn.execute(query, params)
            else:
                cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
        finally:
            await conn.close()

    async def fetch_one(self, query: str, params: tuple = None):
        """Получить одну строку"""
        conn = await self.get_connection()
        try:
            if params:
                cursor = await conn.execute(query, params)
            else:
                cursor = await conn.execute(query)
            row = await cursor.fetchone()
            await cursor.close()
            return row
        finally:
            await conn.close()

    async def init_db(self):
        """Инициализация базы данных"""
        conn = await self.get_connection()
        try:
            # СНАЧАЛА создаем таблицу преподавателей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    email TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # ПОТОМ таблицу предметов с teacher_id
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher TEXT NOT NULL,  -- сохраняем для обратной совместимости
                    teacher_id INTEGER,     -- НОВОЕ: ссылка на teachers.id
                    subject_name TEXT NOT NULL,
                    total_hours INTEGER NOT NULL DEFAULT 0,
                    remaining_hours INTEGER NOT NULL DEFAULT 0,
                    priority INTEGER DEFAULT 1,           -- НОВОЕ
                    color TEXT DEFAULT '#3b82f6',         -- НОВОЕ  
                    notes TEXT,                           -- НОВОЕ
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(teacher, subject_name),
                    FOREIGN KEY (teacher_id) REFERENCES teachers (id)
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

            # Таблица настроек
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица заблокированных слотов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS blocked_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,  -- YYYY-MM-DD
                    slot INTEGER NOT NULL CHECK(slot >= 0 AND slot <= 3),
                    reason TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, slot)
                )
            ''')

            # Таблица снимков недель
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS week_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_start DATE NOT NULL,  -- начало недели
                    snapshot_data TEXT NOT NULL,  -- JSON с занятиями
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.commit()
            print("✅ Все таблицы созданы успешно")
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")
            raise
        finally:
            await conn.close()


# Глобальный экземпляр базы данных
database = Database()
