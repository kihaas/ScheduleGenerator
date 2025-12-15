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


    async def get_subjects_for_group(self, group_id: int) -> List[Subject]:
        """Получить предметы для конкретной группы"""
        return await subject_service.get_all_subjects(group_id)

    async def generate(self, subjects: List[Subject], negative_filters: Dict, group_id: int = 1) -> List[Lesson]:
        """Сгенерировать расписание для группы с проверкой конфликтов между группами"""
        print(f"🎯 Генерация расписания для группы {group_id}")
        print(f"📚 Предметов: {len(subjects)}")

        lessons = []
        days = [0, 1, 2, 3, 4]  # Пн-Пт
        time_slots = [0, 1, 2, 3]  # 4 пары в день

        # Создаем копии предметов для отслеживания
        subject_pool = []
        for subject in subjects:
            # Проверяем что есть пары для распределения
            if subject.remaining_pairs > 0:
                for _ in range(subject.remaining_pairs):
                    subject_pool.append({
                        'id': subject.id,
                        'teacher': subject.teacher,
                        'subject_name': subject.subject_name,
                        'max_per_day': subject.max_per_day,
                        'priority': subject.priority
                    })

        print(f"📊 Всего пар для распределения: {len(subject_pool)}")

        if not subject_pool:
            print("⚠️ Нет пар для распределения")
            return []

        random.shuffle(subject_pool)

        # Словарь для отслеживания использования в день
        daily_usage = {}

        # Заполняем расписание
        for day in days:
            daily_usage[day] = {}

            for time_slot in time_slots:
                if not subject_pool:
                    break

                # Ищем подходящий предмет
                found_index = -1

                for i, subject in enumerate(subject_pool):
                    teacher = subject['teacher']
                    subject_name = subject['subject_name']
                    key = f"{teacher}_{subject_name}"

                    # Проверяем max_per_day
                    if key in daily_usage[day]:
                        if daily_usage[day][key] >= subject['max_per_day']:
                            continue

                    # Проверяем доступность преподавателя
                    if not self._is_teacher_available(teacher, day, time_slot, negative_filters):
                        continue

                    # Проверяем что преподаватель не занят в других группах
                    if not await self._is_teacher_free_across_groups(teacher, day, time_slot, group_id):
                        continue

                    found_index = i
                    break

                if found_index >= 0:
                    subject = subject_pool.pop(found_index)
                    teacher = subject['teacher']
                    subject_name = subject['subject_name']
                    key = f"{teacher}_{subject_name}"

                    # Создаем урок
                    lesson = Lesson(
                        day=day,
                        time_slot=time_slot,
                        teacher=teacher,
                        subject_name=subject_name,
                        editable=True
                    )
                    lessons.append(lesson)

                    # Обновляем счетчик использования в день
                    if key in daily_usage[day]:
                        daily_usage[day][key] += 1
                    else:
                        daily_usage[day][key] = 1

        print(f"✅ Сгенерировано уроков: {len(lessons)}")
        print(f"📊 Осталось нераспределенных пар: {len(subject_pool)}")

        from app.services.subject_services import subject_service

        # Считаем сколько пар каждого предмета сгенерировано
        subject_counts = {}
        for lesson in lessons:
            key = (lesson.teacher, lesson.subject_name)
            subject_counts[key] = subject_counts.get(key, 0) + 1

        # Вычитаем часы для каждого предмета
        for (teacher, subject_name), pair_count in subject_counts.items():
            # Находим ID предмета
            subject = await database.fetch_one(
                'SELECT id FROM subjects WHERE teacher = ? AND subject_name = ? AND group_id = ?',
                (teacher, subject_name, group_id)
            )
            if subject:
                subject_id = subject[0]
                # Вычитаем часы (2 часа на пару * количество пар)
                hours_to_subtract = pair_count * 2
                success = await subject_service.update_subject_hours(subject_id, hours_to_subtract)
                if success:
                    print(f"✅ Вычтено {hours_to_subtract}ч для {teacher} - {subject_name}")

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