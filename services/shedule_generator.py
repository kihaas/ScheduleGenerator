from typing import List, Dict, Tuple
import random

from app.db import database
from app.db.models import Lesson, Subject
from app.services.subject_services import subject_service


class ScheduleGenerator:
    """Slot-first генератор расписания для unit-тестирования"""

    def __init__(self):
        self.occupied_slots = set()

    async def generate_schedule(self) -> List[Lesson]:
        """Генерация расписания"""
        print("🔄 Начинаем генерацию расписания...")

        subjects = await subject_service.get_all_subjects()
        print(f"📚 Найдено предметов: {len(subjects)}")

        if not subjects:
            print("❌ Нет предметов для генерации")
            return []

        # Очищаем текущее расписание
        await database.execute('DELETE FROM lessons')

        # Сбрасываем remaining_pairs для всех предметов
        for subject in subjects:
            await database.execute(
                'UPDATE subjects SET remaining_pairs = ?, remaining_hours = ? WHERE id = ?',
                (subject.total_hours // 2, subject.total_hours, subject.id)
            )

        # Перезагружаем предметы с обновленными данными
        subjects = await subject_service.get_all_subjects()

        # Создаем уроки
        lessons = []
        subject_index = 0

        for day in range(5):  # Пн-Пт
            for time_slot in range(4):  # 4 пары
                if not subjects:
                    break

                # Ищем предмет с оставшимися парами
                subject_found = None
                for i in range(len(subjects)):
                    subject = subjects[(subject_index + i) % len(subjects)]
                    if subject.remaining_pairs > 0:
                        subject_found = subject
                        break

                if not subject_found:
                    break

                lesson = Lesson(
                    day=day,
                    time_slot=time_slot,
                    teacher=subject_found.teacher,
                    subject_name=subject_found.subject_name,
                    editable=True
                )
                lessons.append(lesson)

                # Уменьшаем количество оставшихся пар и часов
                await database.execute(
                    'UPDATE subjects SET remaining_pairs = remaining_pairs - 1, remaining_hours = remaining_hours - 2 WHERE id = ?',
                    (subject_found.id,)
                )

                subject_index += 1

        # Сохраняем уроки
        for lesson in lessons:
            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable) VALUES (?, ?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name, int(lesson.editable))
            )

        print(f"✅ Сгенерировано уроков: {len(lessons)}")

        # Логируем итоговое состояние предметов
        final_subjects = await subject_service.get_all_subjects()
        for subject in final_subjects:
            print(
                f"📊 {subject.teacher} - {subject.subject_name}: {subject.remaining_hours}ч осталось, {subject.remaining_pairs} пар")

        return lessons

    def _initialize_subject_state(self, subjects: List[Subject]) -> Dict[Tuple[str, str], Dict]:
        state = {}
        for subject in subjects:
            key = (subject.teacher, subject.subject_name)
            state[key] = {
                'remaining_pairs': subject.remaining_pairs,
                'priority': subject.priority,
                'max_per_day': subject.max_per_day
            }
        return state

    def _initialize_daily_count(self, subjects: List[Subject], count_type: str) -> Dict:
        daily_count = {}
        for subject in subjects:
            if count_type == 'teacher':
                key = subject.teacher
            else:
                key = (subject.teacher, subject.subject_name)

            daily_count[key] = {day: 0 for day in range(5)}
        return daily_count

    def _get_candidates_for_slot(self, day: int, time_slot: int, subjects: List[Subject],
                                 subject_state: Dict, daily_teacher_count: Dict,
                                 daily_subject_count: Dict, negative_filters: Dict) -> List[Dict]:
        candidates = []

        for subject in subjects:
            teacher = subject.teacher
            subject_key = (teacher, subject.subject_name)
            state = subject_state[subject_key]

            if not self._is_subject_available(teacher, subject_key, state, day, time_slot,
                                              daily_teacher_count, daily_subject_count, negative_filters):
                continue

            weight = self._calculate_candidate_weight(state)

            candidates.append({
                'teacher': teacher,
                'subject_name': subject.subject_name,
                'subject_key': subject_key,
                'weight': weight,
                'state': state
            })

        return candidates

    def _is_subject_available(self, teacher: str, subject_key: Tuple[str, str],
                              state: Dict, day: int, time_slot: int,
                              daily_teacher_count: Dict, daily_subject_count: Dict,
                              negative_filters: Dict) -> bool:

        if state['remaining_pairs'] <= 0:
            return False

        restrictions = negative_filters.get(teacher, {})
        if day in restrictions.get('restricted_days', []):
            return False
        if time_slot in restrictions.get('restricted_slots', []):
            return False

        if daily_teacher_count[teacher][day] >= 4:
            return False

        if daily_subject_count[subject_key][day] >= state['max_per_day']:
            return False

        # Проверка что преподаватель не занят в этом слоте
        if any(lesson.teacher == teacher for lesson in self._get_lessons_in_slot(day, time_slot)):
            return False

        return True

    def _get_lessons_in_slot(self, day: int, time_slot: int) -> List[Lesson]:
        """Вспомогательный метод для получения уроков в указанном слоте"""
        # В реальной реализации это будет обращение к списку lessons
        # Для тестирования можно мокировать
        return []

    def _calculate_candidate_weight(self, state: Dict) -> float:
        if state['priority'] > 0:
            return float(state['priority'])
        else:
            return max(1.0, float(state['remaining_pairs']))

    def _select_candidate(self, candidates: List[Dict]) -> Dict:
        if not candidates:
            return None

        weights = [candidate['weight'] for candidate in candidates]
        selected = random.choices(candidates, weights=weights, k=1)[0]
        return selected

    def _update_state_after_selection(self, selected: Dict, day: int,
                                      subject_state: Dict, daily_teacher_count: Dict,
                                      daily_subject_count: Dict):
        teacher = selected['teacher']
        subject_key = selected['subject_key']

        subject_state[subject_key]['remaining_pairs'] -= 1
        daily_teacher_count[teacher][day] += 1
        daily_subject_count[subject_key][day] += 1


# Глобальный экземпляр для тестирования
schedule_generator = ScheduleGenerator()