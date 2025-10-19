-- Создание таблицы для сохраненных расписаний
CREATE TABLE IF NOT EXISTS saved_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload TEXT NOT NULL
);

-- Индекс для быстрого поиска по имени и дате
CREATE INDEX IF NOT EXISTS idx_saved_schedules_name ON saved_schedules(name);
CREATE INDEX IF NOT EXISTS idx_saved_schedules_created_at ON saved_schedules(created_at DESC);



