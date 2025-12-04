from typing import List, Dict, Tuple
import random
import json

from app.db.database import database
from app.db.models import Lesson, Subject
from app.services.subject_services import subject_service
from app.services.negative_filters_service import negative_filters_service


class ScheduleGenerator:
    """Улучшенный генератор расписания с проверкой конфликтов между группами"""

    def __init__(self):
        self.occupied_slots = set()

    async def generate_schedule(self, group_id: int = 1) -> List[Lesson]:
        """Генерация расписания для конкретной группы"""
        print(f"🔄 Начинаем генерацию расписания для группы {group_id}...")

        # Получаем предметы для конкретной группы
        subjects = await subject_service.get_all_subjects(group_id)
        print(f"📚 Найдено предметов в группе {group_id}: {len(subjects)}")

        if not subjects:
            print("❌ Нет предметов для генерации")
            return []

        # Получаем ГЛОБАЛЬНЫЕ фильтры
        negative_filters = await subject_service.get_negative_filters()  # БЕЗ group_id
        print(f"🎯 Глобальных ограничений: {len(negative_filters)}")

        # Генерируем расписание с проверкой конфликтов
        lessons = await self.generate(subjects, negative_filters, group_id)

        # Очищаем старые уроки группы
        await database.execute(
            'DELETE FROM lessons WHERE group_id = ?',
            (group_id,)
        )

        # Сохраняем уроки
        for lesson in lessons:
            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable, group_id) VALUES (?, ?, ?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name, int(lesson.editable), group_id)
            )

        # Обновляем часы предметов
        for lesson in lessons:
            await database.execute(
                '''UPDATE subjects 
                   SET remaining_hours = remaining_hours - 2, 
                       remaining_pairs = remaining_pairs - 1 
                   WHERE teacher = ? AND subject_name = ? AND group_id = ?''',
                (lesson.teacher, lesson.subject_name, group_id)
            )

        print(f"✅ Сгенерировано уроков для группы {group_id}: {len(lessons)}")

        return lessons

    async def get_subjects_for_group(self, group_id: int) -> List[Subject]:
        """Получить предметы для конкретной группы"""
        return await subject_service.get_all_subjects(group_id)

    async def generate(self, subjects: List[Subject], negative_filters: Dict, group_id: int = 1) -> List[Lesson]:
        """Сгенерировать расписание для группы с проверкой конфликтов между группами"""
        print(f"🎯 Генерация расписания для группы {group_id}")
        print(f"📚 Предметов: {len(subjects)}, Ограничений: {len(negative_filters)}")

        lessons = []
        days = [0, 1, 2, 3, 4]  # Пн-Пт
        time_slots = [0, 1, 2, 3]  # 4 пары в день

        # Сортируем предметы по приоритету (сначала высокий приоритет)
        sorted_subjects = sorted(subjects, key=lambda x: x.priority, reverse=True)

        # Создаем копию для отслеживания оставшихся пар
        remaining_subjects = []
        for subject in sorted_subjects:
            for _ in range(subject.remaining_pairs):
                remaining_subjects.append(subject)

        random.shuffle(remaining_subjects)

        # Словарь для отслеживания распределенных часов
        hours_allocated = {}

        # Заполняем расписание
        for day in days:
            daily_subjects = {}  # Для отслеживания max_per_day

            for time_slot in time_slots:
                if not remaining_subjects:
                    break

                # Пытаемся найти подходящий предмет
                subject_found = None
                subject_index = -1

                for i, subject in enumerate(remaining_subjects):
                    teacher = subject.teacher

                    # Проверяем локальные ограничения преподавателя
                    if not self._is_teacher_available(teacher, day, time_slot, negative_filters):
                        continue

                    # Проверяем max_per_day
                    if subject.subject_name in daily_subjects:
                        if daily_subjects[subject.subject_name] >= subject.max_per_day:
                            continue

                    # 🔥 ВАЖНО: Проверяем что преподаватель не занят в это время В ЛЮБОЙ ГРУППЕ
                    if not await self._is_teacher_free_across_groups(teacher, day, time_slot, group_id):
                        print(f"🚫 Преподаватель {teacher} занят в день {day}, слот {time_slot} в другой группе")
                        continue

                    subject_found = subject
                    subject_index = i
                    break

                if subject_found:
                    # Создаем урок
                    lesson = Lesson(
                        day=day,
                        time_slot=time_slot,
                        teacher=subject_found.teacher,
                        subject_name=subject_found.subject_name,
                        editable=True
                    )
                    lessons.append(lesson)

                    # Обновляем счетчики
                    if subject_found.subject_name in daily_subjects:
                        daily_subjects[subject_found.subject_name] += 1
                    else:
                        daily_subjects[subject_found.subject_name] = 1

                    # Отмечаем выделенные часы
                    key = (subject_found.teacher, subject_found.subject_name)
                    hours_allocated[key] = hours_allocated.get(key, 0) + 2

                    # Удаляем использованный предмет
                    remaining_subjects.pop(subject_index)

        print(f"✅ Сгенерировано уроков: {len(lessons)}")
        print(f"📊 Осталось нераспределенных пар: {len(remaining_subjects)}")
        print(f"📊 Распределено часов: {hours_allocated}")

        return lessons

    def _is_teacher_available(self, teacher: str, day: int, time_slot: int, negative_filters: Dict) -> bool:
        """Проверить доступность преподавателя по его ГЛОБАЛЬНЫМ ограничениям"""
        if teacher not in negative_filters:
            return True

        filters = negative_filters[teacher]

        # Проверяем ограничения по дням
        if day in filters.get('restricted_days', []):
            print(f"🚫 {teacher} недоступен в день {day} (глобальное ограничение)")
            return False

        # Проверяем ограничения по слотам
        if time_slot in filters.get('restricted_slots', []):
            print(f"🚫 {teacher} недоступен в слот {time_slot} (глобальное ограничение)")
            return False

        return True

    async def _is_teacher_free_across_groups(self, teacher: str, day: int, time_slot: int,
                                             current_group_id: int) -> bool:
        """Проверить что преподаватель свободен в это время ВО ВСЕХ ДРУГИХ ГРУППАХ"""
        try:
            # Ищем есть ли у этого преподавателя урок в это время в ЛЮБОЙ ДРУГОЙ группе
            existing_lesson = await database.fetch_one(
                'SELECT id FROM lessons WHERE teacher = ? AND day = ? AND time_slot = ? AND group_id != ?',
                (teacher, day, time_slot, current_group_id)
            )

            return existing_lesson is None  # True = свободен, False = занят в другой группе

        except Exception as e:
            print(f"❌ Ошибка проверки занятости преподавателя {teacher}: {e}")
            return True  # В случае ошибки разрешаем поставить пару

    async def can_assign_teacher(self, teacher: str, day: int, time_slot: int, current_group_id: int = 1) -> bool:
        """Проверить, можно ли назначить преподавателя в этот слот"""
        # 1. Проверяем локальные ограничения (фильтры группы)
        local_available = await negative_filters_service.check_teacher_availability(teacher, day, time_slot,
                                                                                    current_group_id)

        if not local_available:
            return False

        # 2. Проверяем что преподаватель свободен в других группах
        global_available = await self._is_teacher_free_across_groups(teacher, day, time_slot, current_group_id)

        return local_available and global_available


# Глобальный экземпляр
schedule_generator = ScheduleGenerator()