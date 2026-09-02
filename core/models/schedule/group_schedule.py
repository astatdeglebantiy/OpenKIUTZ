from datetime import datetime
from zoneinfo import ZoneInfo
from core.models.schedule.lesson import LessonItem


class GroupSchedule:
    def __init__(
        self,
        group_name: str,
        ref_date_str: str,
        time_slots: list[str],
        subjects_map: dict[str, dict],
        weeks_data: list[dict[str, list[str | None]]]
    ):
        self.group_name: str = group_name
        self.ref_date_str: str = ref_date_str
        self.time_slots: list[str] = time_slots
        self.subjects_map: dict[str, dict] = subjects_map
        self.weeks_data: list[dict[str, list[str | None]]] = weeks_data

    @property
    def total_weeks(self) -> int:
        return len(self.weeks_data)

    def get_current_week_number(self, tz: ZoneInfo) -> int:
        if self.total_weeks <= 1:
            return 1
        try:
            ref_date = datetime.strptime(self.ref_date_str, "%Y-%m-%d")
        except ValueError:
            return 1

        now = datetime.now(tz).replace(tzinfo=None)
        delta_days = (now - ref_date).days
        weeks_passed = delta_days // 7
        return (weeks_passed % self.total_weeks) + 1

    def get_day_lessons(self, week_index: int, day_number: int) -> list[LessonItem]:
        if week_index < 0 or week_index >= self.total_weeks:
            return []

        day_str = str(day_number)
        lessons_ids = self.weeks_data[week_index].get(day_str, [])
        result = []

        for idx, sub_id in enumerate(lessons_ids, start=1):
            time_str = self.time_slots[idx - 1] if idx - 1 < len(self.time_slots) else ""
            if sub_id and sub_id in self.subjects_map:
                sub = self.subjects_map[sub_id]
                result.append(
                    LessonItem(
                        number=idx,
                        time_slot=time_str,
                        name=sub.get("name", sub_id),
                        lecturer=sub.get("lecturers_name", "—") or "—",
                        room=sub.get("room", "") or "",
                        link=sub.get("link", "") or ""
                    )
                )
            else:
                result.append(
                    LessonItem(
                        number=idx,
                        time_slot=time_str,
                        name="",
                        lecturer="—",
                        room="",
                        link=""
                    )
                )
        return result
