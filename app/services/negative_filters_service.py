from app.db.database import database
import json
from typing import Dict, List, Optional


class NegativeFiltersService:
    async def save_negative_filter(self, teacher: str, restricted_days: List[int], restricted_slots: List[int]) -> bool:
        """Сохранить ГЛОБАЛЬНЫЕ ограничения для преподавателя"""
        try:
            await database.execute(
                'INSERT OR REPLACE INTO negative_filters (teacher, restricted_days, restricted_slots) VALUES (?, ?, ?)',
                (teacher, json.dumps(restricted_days), json.dumps(restricted_slots))
            )
            print(f"✅ Глобальные ограничения сохранены для {teacher}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения глобальных ограничений: {e}")
            return False

    async def get_negative_filters(self) -> Dict:
        """Получить ВСЕ глобальные ограничения"""
        try:
            # ПРЯМОЙ запрос без group_id
            rows = await database.fetch_all(
                'SELECT teacher, restricted_days, restricted_slots FROM negative_filters'
            )

            filters = {}
            for row in rows:
                teacher, days_json, slots_json = row
                try:
                    filters[teacher] = {
                        "restricted_days": json.loads(days_json) if days_json else [],
                        "restricted_slots": json.loads(slots_json) if slots_json else []
                    }
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON для {teacher}: {e}")
                    filters[teacher] = {
                        "restricted_days": [],
                        "restricted_slots": []
                    }

            print(f"✅ Загружено {len(filters)} ГЛОБАЛЬНЫХ фильтров")
            return filters
        except Exception as e:
            print(f"❌ Ошибка получения глобальных ограничений: {e}")
            # Возвращаем пустой словарь в случае ошибки
            return {}

    async def get_teacher_filters(self, teacher: str) -> Optional[Dict]:
        """Получить глобальные ограничения для конкретного преподавателя"""
        try:
            row = await database.fetch_one(
                'SELECT restricted_days, restricted_slots FROM negative_filters WHERE teacher = ?',
                (teacher,)
            )

            if row:
                days_json, slots_json = row
                return {
                    "restricted_days": json.loads(days_json) if days_json else [],
                    "restricted_slots": json.loads(slots_json) if slots_json else []
                }
            return None
        except Exception as e:
            print(f"❌ Ошибка получения ограничений для {teacher}: {e}")
            return None

    async def remove_negative_filter(self, teacher: str) -> bool:
        """Удалить глобальные ограничения для преподавателя"""
        try:
            await database.execute(
                'DELETE FROM negative_filters WHERE teacher = ?',
                (teacher,)
            )
            print(f"✅ Глобальные ограничения удалены для {teacher}")
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления глобальных ограничений: {e}")
            return False

    async def check_teacher_availability(self, teacher: str, day: int, time_slot: int) -> bool:
        """Проверить, доступен ли преподаватель глобально в указанный день и слот"""
        try:
            filters = await self.get_teacher_filters(teacher)
            if not filters:
                return True  # Нет ограничений - доступен

            # Проверяем ограничения по дням
            if day in filters.get('restricted_days', []):
                print(f"🚫 {teacher} недоступен в день {day} (ограничение по дню)")
                return False

            # Проверяем ограничения по слотам
            if time_slot in filters.get('restricted_slots', []):
                print(f"🚫 {teacher} недоступен в слот {time_slot} (ограничение по слоту)")
                return False

            return True
        except Exception as e:
            print(f"❌ Ошибка проверки глобальной доступности: {e}")
            return True


# Глобальный экземпляр сервиса
negative_filters_service = NegativeFiltersService()