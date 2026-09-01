from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

KYIV_TZ = ZoneInfo("Europe/Kyiv")

@dataclass
class Subject:
    name: str
    link: str = ""
    audience: Optional[str] = ""

@dataclass
class AcademicContext:
    reference_date: str  # "YYYY-MM-DD"
    reference_week: int  # 1 or 2

@dataclass
class SaturdayRef:
    week: int
    day: int

@dataclass
class ScheduleConfig:
    subjects: Dict[str, Subject]
    schedule: List[Dict[int, List[Optional[Subject]]]]  # [Неделя 1, Неделя 2]
    time_slots: List[str]
    academic_context: AcademicContext
    saturday_schedule: Dict[str, SaturdayRef] = field(default_factory=dict)
    offline_days: List[int] = field(default_factory=list)

    @property
    def total_weeks(self) -> int:
        return len(self.schedule) or 1

    @property
    def current_week_number(self) -> int:
        return self.get_week_for_date(datetime.now(KYIV_TZ))

    def get_week_for_date(self, date: datetime) -> int:
        try:
            ref_date = datetime.strptime(self.academic_context.reference_date, "%Y-%m-%d")
        except ValueError:
            return 1

        delta_days = (date.replace(tzinfo=None) - ref_date).days
        weeks_passed = delta_days // 7
        return (self.academic_context.reference_week - 1 + weeks_passed) % self.total_weeks + 1

    def get_day_lessons(self, week_idx: int, day_idx: int) -> List[Optional[Subject]]:
        if week_idx < 0 or week_idx >= len(self.schedule):
            return []
        # day_idx: 1 - Mon, 2 - Tue ... 7 - Sun
        return self.schedule[week_idx].get(day_idx, [])