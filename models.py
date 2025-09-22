from pydantic import BaseModel
from typing import Optional, List, Dict, Set
from datetime import datetime

class Subject(BaseModel):
    id: Optional[int] = None
    teacher: str
    subject_name: str
    total_hours: int
    remaining_hours: int

class Lesson(BaseModel):
    day: int
    time_slot: int
    teacher: str
    subject_name: str
    is_past: bool = False

class NegativeFilter(BaseModel):
    teacher: str
    restricted_days: Set[int] = set()  # Дни, когда нельзя ставить (0-6)
    restricted_slots: Set[int] = set()  # Пары, когда нельзя ставить (0-3)

class ScheduleData(BaseModel):
    subjects: List[Subject]
    lessons: List[Lesson]
    negative_filters: Dict[str, NegativeFilter] = {}  # key: teacher name