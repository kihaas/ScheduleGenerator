import sqlite3
import json
from typing import List, Dict, Set
from models import Subject, Lesson, NegativeFilter


class Database:
    def __init__(self, db_name="schedule.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                total_hours INTEGER NOT NULL,
                remaining_hours INTEGER NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day INTEGER NOT NULL,
                time_slot INTEGER NOT NULL,
                teacher TEXT NOT NULL,
                subject_name TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS negative_filters (
                teacher TEXT PRIMARY KEY,
                restricted_days TEXT,
                restricted_slots TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_subjects(self, subjects: List[Subject]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM subjects')

        for subject in subjects:
            cursor.execute(
                'INSERT INTO subjects (teacher, subject_name, total_hours, remaining_hours) VALUES (?, ?, ?, ?)',
                (subject.teacher, subject.subject_name, subject.total_hours, subject.remaining_hours)
            )

        conn.commit()
        conn.close()

    def get_subjects(self) -> List[Subject]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT id, teacher, subject_name, total_hours, remaining_hours FROM subjects')
        rows = cursor.fetchall()

        subjects = []
        for row in rows:
            subjects.append(Subject(
                id=row[0],
                teacher=row[1],
                subject_name=row[2],
                total_hours=row[3],
                remaining_hours=row[4]
            ))

        conn.close()
        return subjects

    def save_lessons(self, lessons: List[Lesson]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM lessons')

        for lesson in lessons:
            cursor.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name) VALUES (?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name)
            )

        conn.commit()
        conn.close()

    def get_lessons(self) -> List[Lesson]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT day, time_slot, teacher, subject_name FROM lessons')
        rows = cursor.fetchall()

        lessons = []
        for row in rows:
            lessons.append(Lesson(
                day=row[0],
                time_slot=row[1],
                teacher=row[2],
                subject_name=row[3]
            ))

        conn.close()
        return lessons

    def save_negative_filters(self, negative_filters: Dict[str, NegativeFilter]):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM negative_filters')

        for teacher, filter_data in negative_filters.items():
            restricted_days = json.dumps(list(filter_data.restricted_days))
            restricted_slots = json.dumps(list(filter_data.restricted_slots))

            cursor.execute(
                'INSERT INTO negative_filters (teacher, restricted_days, restricted_slots) VALUES (?, ?, ?)',
                (teacher, restricted_days, restricted_slots)
            )

        conn.commit()
        conn.close()

    def get_negative_filters(self) -> Dict[str, NegativeFilter]:
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT teacher, restricted_days, restricted_slots FROM negative_filters')
        rows = cursor.fetchall()

        negative_filters = {}
        for row in rows:
            restricted_days = set(json.loads(row[1])) if row[1] else set()
            restricted_slots = set(json.loads(row[2])) if row[2] else set()

            negative_filters[row[0]] = NegativeFilter(
                teacher=row[0],
                restricted_days=restricted_days,
                restricted_slots=restricted_slots
            )

        conn.close()
        return negative_filters

    def clear_all(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM subjects')
        cursor.execute('DELETE FROM lessons')
        cursor.execute('DELETE FROM negative_filters')

        conn.commit()
        conn.close()