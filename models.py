from pydantic import BaseModel
from typing import Optional, List
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

class ScheduleData(BaseModel):
    subjects: List[Subject]
    lessons: List[Lesson]