-- Создание таблицы преподавателей
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Обновление таблицы subjects для поддержки teacher_id
ALTER TABLE subjects ADD COLUMN teacher_id INTEGER;
ALTER TABLE subjects ADD COLUMN priority INTEGER DEFAULT 0;
ALTER TABLE subjects ADD COLUMN max_per_day INTEGER DEFAULT 2;

-- Обновление таблицы lessons для поддержки teacher_id
ALTER TABLE lessons ADD COLUMN teacher_id INTEGER;

-- Обновление таблицы negative_filters для поддержки teacher_id
ALTER TABLE negative_filters ADD COLUMN teacher_id INTEGER;

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_subjects_teacher_id ON subjects(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lessons_teacher_id ON lessons(teacher_id);
CREATE INDEX IF NOT EXISTS idx_negative_filters_teacher_id ON negative_filters(teacher_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Перенос существующих данных преподавателей
INSERT OR IGNORE INTO teachers (name)
SELECT DISTINCT teacher_name FROM subjects WHERE teacher_name IS NOT NULL;

-- Обновление teacher_id в subjects
UPDATE subjects
SET teacher_id = (SELECT id FROM teachers WHERE teachers.name = subjects.teacher_name)
WHERE teacher_id IS NULL;

-- Обновление teacher_id в lessons
UPDATE lessons
SET teacher_id = (SELECT id FROM teachers WHERE teachers.name = lessons.teacher_name)
WHERE teacher_id IS NULL AND teacher_name IS NOT NULL;

-- Обновление teacher_id в negative_filters
UPDATE negative_filters
SET teacher_id = (SELECT id FROM teachers WHERE teachers.name = negative_filters.teacher_name)
WHERE teacher_id IS NULL AND teacher_name IS NOT NULL;