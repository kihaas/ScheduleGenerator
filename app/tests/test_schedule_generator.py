import pytest
import asyncio
from app.services.schedule_services import ScheduleService
from app.db.models import Subject, Lesson
from app.services.shedule_generator import ScheduleGenerator


class TestScheduleGenerator:

    @pytest.fixture
    def generator(self):
        return ScheduleGenerator()

    @pytest.fixture
    def sample_subjects(self):
        return [
            Subject(
                teacher="Преподаватель 1",
                subject_name="Математика",
                total_hours=10,
                remaining_hours=10,
                remaining_pairs=5,
                priority=0,
                max_per_day=2
            ),
            Subject(
                teacher="Преподаватель 2",
                subject_name="Физика",
                total_hours=8,
                remaining_hours=8,
                remaining_pairs=4,
                priority=1,
                max_per_day=1
            )
        ]

    @pytest.fixture
    def empty_filters(self):
        return {}

    @pytest.mark.asyncio
    async def test_generate_schedule_empty_subjects(self, generator):
        lessons = await generator.generate_schedule([], {})
        assert lessons == []

    @pytest.mark.asyncio
    async def test_generate_schedule_basic(self, generator, sample_subjects, empty_filters):
        lessons = await generator.generate_schedule(sample_subjects, empty_filters)

        assert len(lessons) > 0
        assert all(isinstance(lesson, Lesson) for lesson in lessons)

        # Проверяем что все уроки в правильных диапазонах
        for lesson in lessons:
            assert 0 <= lesson.day < 5
            assert 0 <= lesson.time_slot < 4

    @pytest.mark.asyncio
    async def test_generate_schedule_with_negative_filters(self, generator, sample_subjects):
        negative_filters = {
            "Преподаватель 1": {
                "restricted_days": [0],  # Не может в понедельник
                "restricted_slots": [0]  # Не может в первую пару
            }
        }

        lessons = await generator.generate_schedule(sample_subjects, negative_filters)

        # Проверяем что ограничения соблюдены
        for lesson in lessons:
            if lesson.teacher == "Преподаватель 1":
                assert lesson.day != 0  # Не понедельник
                assert lesson.time_slot != 0  # Не первая пара


if __name__ == "__main__":
    pytest.main()