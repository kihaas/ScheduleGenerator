
from pydantic import BaseModel
from typing import Optional, List, Dict, Set
import json


class SubjectBase(BaseModel):
    teacher: str
    subject_name: str
    total_hours: int
    remaining_hours: int


class SubjectCreate(SubjectBase):
    pass


class Subject(SubjectBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    day: int
    time_slot: int
    teacher: str
    subject_name: str


class LessonCreate(LessonBase):
    pass


class Lesson(LessonBase):
    id: Optional[int] = None
    is_past: bool = False

    class Config:
        from_attributes = True


class NegativeFilterBase(BaseModel):
    teacher: str
    restricted_days: Set[int] = set()
    restricted_slots: Set[int] = set()


class NegativeFilterCreate(NegativeFilterBase):
    pass


class NegativeFilter(NegativeFilterBase):
    class Config:
        from_attributes = True


class ScheduleData(BaseModel):
    subjects: List[Subject]
    lessons: List[Lesson]
    negative_filters: Dict[str, NegativeFilter] = {}
