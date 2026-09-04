import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import config
from core.models import GroupSchedule, LessonItem


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
            return f"| {lesson.number} | {lesson.time_slot} | — | — | — | — | — |"
        aud = f"`{lesson.room}`" if lesson.room else "—"
        link = f"[Join]({lesson.link})" if lesson.link else "—"
        meet = f"[Join]({lesson.meet})" if lesson.meet else "—"
        return f"| {lesson.number} | {lesson.time_slot} | **{lesson.name}** | {lesson.lecturer} | {aud} | {link} | {meet} |"

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
                active_badge = " ⭐" if week_num == current_week else ""
                output.append(f"## Тиждень {week_num}{active_badge}")

            for day_num in range(1, 7):
                lessons = schedule.get_day_lessons(w_idx, day_num)
                if not any(not l.is_empty for l in lessons):
                    continue

                day_header = "###" if schedule.total_weeks > 1 else "##"
                output.append(f"{day_header} {self.day_names[day_num - 1]}")
                output.append("| № | Час | Дисципліна | Викладач | Авд. | Classroom | Meet |")
                output.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

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
            return f"> **Сьогодні — {self.day_names[day_idx - 1]} {now:%d.%m.%Y} — пар немає.**"

        output = [
            f"### Розклад на сьогодні — {self.day_names[day_idx - 1]} {now:%d.%m.%Y}",
            "| № | Час | Дисципліна | Викладач | Авд. | Classroom | Meet |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
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
