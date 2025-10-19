-- Миграция для добавления новых полей в таблицы subjects и lessons

-- Добавляем новые поля в таблицу subjects
ALTER TABLE subjects ADD COLUMN remaining_pairs INTEGER;
ALTER TABLE subjects ADD COLUMN priority INTEGER DEFAULT 0;
ALTER TABLE subjects ADD COLUMN max_per_day INTEGER DEFAULT 2;

-- Обновляем existing данные: remaining_pairs = remaining_hours / 2
UPDATE subjects SET remaining_pairs = remaining_hours / 2 WHERE remaining_pairs IS NULL;

-- Добавляем поле editable в таблицу lessons
ALTER TABLE lessons ADD COLUMN editable BOOLEAN DEFAULT 1;

-- Создаем индекс для оптимизации запросов по дням и слотам
CREATE INDEX IF NOT EXISTS idx_lessons_day_time ON lessons(day, time_slot);
CREATE INDEX IF NOT EXISTS idx_subjects_teacher ON subjects(teacher);