import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import config


class LessonItem:
    def __init__(self, number: int, time_slot: str, name: str, lecturer: str, room: str, link: str):
        self.number: int = number
        self.time_slot: str = time_slot
        self.name: str = name
        self.lecturer: str = lecturer
        self.room: str = room
        self.link: str = link

    @property
    def is_empty(self) -> bool:
        return not self.name


class GroupSchedule:
    def __init__(
        self,
        group_name: str,
        ref_date_str: str,
        time_slots: list[str],
        subjects_map: dict[str, dict],
        weeks_data: list[dict[str, list[Optional[str]]]]
    ):
        self.group_name: str = group_name
        self.ref_date_str: str = ref_date_str
        self.time_slots: list[str] = time_slots
        self.subjects_map: dict[str, dict] = subjects_map
        self.weeks_data: list[dict[str, list[Optional[str]]]] = weeks_data

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


class ScheduleRepository:
    def __init__(self, schedules_dir: Path | None = None):
        self.schedules_dir: Path = schedules_dir or (config.BASE_DIR / "schedules")
        self.schedules_dir.mkdir(exist_ok=True)
        self._cache: dict[str, GroupSchedule] = {}

    def get_by_group(self, group_name: str) -> Optional[GroupSchedule]:
        if group_name in self._cache:
            return self._cache[group_name]

        file_path = self.schedules_dir / f"{group_name}.json"
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            schedule = GroupSchedule(
                group_name=group_name,
                ref_date_str=data.get("ref_date", "2026-09-01"),
                time_slots=data.get("time", []),
                subjects_map=data.get("subjects", {}),
                weeks_data=data.get("schedule", [])
            )
            self._cache[group_name] = schedule
            return schedule
        except Exception:
            return None

    def clear_cache(self) -> None:
        self._cache.clear()


class ScheduleMarkdownRenderer:
    def __init__(self, day_names: list[str] | None = None, tz: ZoneInfo | None = None):
        self.day_names: list[str] = day_names or [
            "Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"
        ]
        self.tz: ZoneInfo = tz or ZoneInfo("Europe/Kyiv")

    @staticmethod
    def render_row(lesson: LessonItem) -> str:
        if lesson.is_empty:
            return f"| {lesson.number} | {lesson.time_slot} | — | — | — | — |"
        aud = f"`{lesson.room}`" if lesson.room else "—"
        link = f"[Приєднатися]({lesson.link})" if lesson.link else "—"
        return f"| {lesson.number} | {lesson.time_slot} | **{lesson.name}** | {lesson.lecturer} | {aud} | {link} |"

    def render_full(self, schedule: GroupSchedule) -> str:
        if schedule.total_weeks == 0:
            return f"> Розклад для групи **{schedule.group_name}** порожній."

        output = []
        current_week = schedule.get_current_week_number(self.tz)

        if schedule.total_weeks > 1:
            output.append(f"> **Поточний тиждень:** {current_week}-й\n")

        for w_idx in range(schedule.total_weeks):
            week_num = w_idx + 1

            if schedule.total_weeks > 1:
                active_badge = " ⭐ (Поточний)" if week_num == current_week else ""
                output.append(f"## Тиждень {week_num}{active_badge}")

            for day_num in range(1, 7):
                lessons = schedule.get_day_lessons(w_idx, day_num)
                if not any(not l.is_empty for l in lessons):
                    continue

                day_header = "###" if schedule.total_weeks > 1 else "##"
                output.append(f"{day_header} {self.day_names[day_num - 1]}")
                output.append("| № | Час | Дисципліна | Викладач | Ауд. | Посилання |")
                output.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

                for lesson in lessons:
                    output.append(self.render_row(lesson))
                output.append("")

        return "\n".join(output)

    def render_today(self, schedule: GroupSchedule) -> str:
        now = datetime.now(self.tz)
        day_idx = now.weekday() + 1

        if day_idx > 6:
            return "> **Сьогодні вихідний день.**"

        if schedule.total_weeks == 0:
            return "> **Розклад порожній.**"

        current_week = schedule.get_current_week_number(self.tz)
        lessons = schedule.get_day_lessons(current_week - 1, day_idx)

        if not any(not l.is_empty for l in lessons):
            return f"> **Сьогодні ({self.day_names[day_idx - 1]}) пар немає.**"

        output = [
            f"### Розклад на сьогодні ({self.day_names[day_idx - 1]})",
            "| № | Час | Дисципліна | Викладач | Ауд. | Посилання |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for lesson in lessons:
            output.append(self.render_row(lesson))

        return "\n".join(output)

    def render_composite_template(self, schedule: GroupSchedule) -> str:
        today_block = self.render_today(schedule)
        full_block = self.render_full(schedule)

        return f"""## Пари на сьогодні
{today_block}

---

## Повний розклад занять
{full_block}"""


class ScheduleService:
    def __init__(
        self,
        repository: ScheduleRepository | None = None,
        renderer: ScheduleMarkdownRenderer | None = None
    ):
        self.repository: ScheduleRepository = repository or ScheduleRepository()
        self.renderer: ScheduleMarkdownRenderer = renderer or ScheduleMarkdownRenderer()

    def render_full_template(self, group_name: str) -> str:
        schedule = self.repository.get_by_group(group_name)
        if not schedule:
            return f"> Розклад для групи **{group_name}** ще не додано в систему."
        return self.renderer.render_composite_template(schedule)

    def render_today(self, group_name: str) -> str:
        schedule = self.repository.get_by_group(group_name)
        if not schedule:
            return f"> Розклад для групи **{group_name}** недоступний."
        return self.renderer.render_today(schedule)

    def render_full_schedule(self, group_name: str) -> str:
        schedule = self.repository.get_by_group(group_name)
        if not schedule:
            return f"> Розклад для групи **{group_name}** недоступний."
        return self.renderer.render_full(schedule)


default_schedule_service = ScheduleService()
