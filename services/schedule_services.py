from typing import List, Dict, Tuple
import random
from app.db.database import database
from app.db.models import Lesson, Subject
from app.services.subject_services import subject_service
from app.services.teacher_service import teacher_service


class ScheduleService:
    async def get_all_lessons(self) -> List[Lesson]:
        """Получить все уроки"""
        rows = await database.fetch_all(
            'SELECT id, day, time_slot, teacher, subject_name, editable FROM lessons ORDER BY day, time_slot'
        )
        lessons = []
        for row in rows:
            lesson = Lesson(
                id=row[0],
                day=row[1],
                time_slot=row[2],
                teacher=row[3],
                subject_name=row[4],
                editable=bool(row[5]) if row[5] is not None else True
            )
            lessons.append(lesson)
        return lessons

    async def save_lessons(self, lessons: List[Lesson]):
        """Сохранить уроки"""
        await database.execute('DELETE FROM lessons')

        for lesson in lessons:
            await database.execute(
                'INSERT INTO lessons (day, time_slot, teacher, subject_name, editable) VALUES (?, ?, ?, ?, ?)',
                (lesson.day, lesson.time_slot, lesson.teacher, lesson.subject_name, int(lesson.editable))
            )

    async def generate_schedule(self) -> List[Lesson]:
        """Генерация расписания с учетом ограничений"""
        print("🔄 Начинаем генерацию расписания...")

        subjects = await subject_service.get_all_subjects()
        negative_filters = await subject_service.get_negative_filters()

        print(f"📚 Найдено предметов: {len(subjects)}")
        print(f"🚫 Найдено ограничений: {len(negative_filters)}")

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

        # Создаем уроки с учетом ограничений
        lessons = []
        subject_index = 0

        for day in range(5):  # Пн-Пт
            for time_slot in range(4):  # 4 пары
                if not subjects:
                    break

                # Ищем предмет с оставшимися парами, учитывая ограничения
                subject_found = None
                for i in range(len(subjects)):
                    subject = subjects[(subject_index + i) % len(subjects)]

                    # Проверяем ограничения для преподавателя
                    if subject.teacher in negative_filters:
                        restrictions = negative_filters[subject.teacher]
                        if (day in restrictions.get('restricted_days', []) or
                                time_slot in restrictions.get('restricted_slots', [])):
                            print(f"🚫 Пропускаем {subject.teacher} - ограничения для дня {day}, слота {time_slot}")
                            continue

                    if subject.remaining_pairs > 0:
                        subject_found = subject
                        break

                if not subject_found:
                    continue

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

    async def remove_lesson(self, day: int, time_slot: int) -> bool:
        """Удалить урок"""
        lesson = await database.fetch_one(
            'SELECT teacher, subject_name, editable FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        if not lesson:
            return False

        teacher, subject_name, editable = lesson
        if editable == 0:
            return False

        await database.execute(
            'DELETE FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        # Возвращаем пару
        await database.execute('''
            UPDATE subjects 
            SET remaining_pairs = remaining_pairs + 1,
                remaining_hours = remaining_hours + 2
            WHERE teacher = ? AND subject_name = ?
        ''', (teacher, subject_name))

        return True

    async def update_lesson(self, day: int, time_slot: int, new_teacher: str, new_subject_name: str) -> bool:
        """Обновить урок - заменить на существующий предмет"""
        # Получаем текущий урок
        current_lesson = await database.fetch_one(
            'SELECT teacher, subject_name, editable FROM lessons WHERE day = ? AND time_slot = ?',
            (day, time_slot)
        )

        if not current_lesson or not current_lesson[2]:  # editable check
            return False

        old_teacher, old_subject_name, _ = current_lesson

        # Проверяем существование нового предмета
        new_subject = await database.fetch_one(
            'SELECT id, remaining_pairs FROM subjects WHERE teacher = ? AND subject_name = ?',
            (new_teacher, new_subject_name)
        )

        if not new_subject:
            print(f"❌ Предмет не найден: {new_teacher} - {new_subject_name}")
            return False

        if new_subject[1] <= 0:  # remaining_pairs check
            print(f"❌ Не осталось пар у предмета: {new_teacher} - {new_subject_name}")
            return False

        # Если заменяем на тот же предмет - ничего не делаем
        if old_teacher == new_teacher and old_subject_name == new_subject_name:
            print("ℹ️ Замена на тот же предмет - пропускаем")
            return True

        # Начинаем транзакцию
        try:
            # Возвращаем пару старому предмету
            await database.execute('''
                UPDATE subjects 
                SET remaining_pairs = remaining_pairs + 1,
                    remaining_hours = remaining_hours + 2
                WHERE teacher = ? AND subject_name = ?
            ''', (old_teacher, old_subject_name))

            # Забираем пару у нового предмета
            await database.execute('''
                UPDATE subjects 
                SET remaining_pairs = remaining_pairs - 1,
                    remaining_hours = remaining_hours - 2
                WHERE teacher = ? AND subject_name = ?
            ''', (new_teacher, new_subject_name))

            # Обновляем урок
            await database.execute(
                'UPDATE lessons SET teacher = ?, subject_name = ? WHERE day = ? AND time_slot = ?',
                (new_teacher, new_subject_name, day, time_slot)
            )

            print(f"✅ Замена: {old_teacher} - {old_subject_name} → {new_teacher} - {new_subject_name}")
            return True

        except Exception as e:
            print(f"❌ Ошибка при замене урока: {e}")
            return False

    async def get_statistics(self) -> Dict[str, int]:
        """Получить статистику"""
        try:
            subjects = await subject_service.get_all_subjects()
            lessons = await self.get_all_lessons()
            teachers = await teacher_service.get_all_teachers()

            total_hours = sum(s.total_hours for s in subjects)
            remaining_hours = sum(s.remaining_hours for s in subjects)
            scheduled_pairs = len(lessons)
            remaining_pairs = sum(s.remaining_pairs for s in subjects)

            print(
                f"📊 Статистика: {len(subjects)} предметов, {len(teachers)} преподавателей, {scheduled_pairs} пар, {remaining_hours}ч осталось")

            return {
                'total_subjects': len(subjects),
                'total_teachers': len(teachers),
                'total_hours': total_hours,
                'remaining_hours': remaining_hours,
                'scheduled_pairs': scheduled_pairs,
                'remaining_pairs': remaining_pairs
            }
        except Exception as e:
            print(f"❌ Ошибка в статистике: {e}")
            return {
                'total_subjects': 0,
                'total_teachers': 0,
                'total_hours': 0,
                'remaining_hours': 0,
                'scheduled_pairs': 0,
                'remaining_pairs': 0
            }

    def get_week_days(self):
        return ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

    def get_time_slots(self):
        return [
            {'start': '9:00', 'end': '10:30'},
            {'start': '10:40', 'end': '12:10'},
            {'start': '12:40', 'end': '14:10'},
            {'start': '14:20', 'end': '15:50'}
        ]


# Создаем экземпляр сервиса
schedule_service = ScheduleService()