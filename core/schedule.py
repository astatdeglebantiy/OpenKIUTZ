import json
from datetime import datetime
from zoneinfo import ZoneInfo

import config

KYIV_TZ = ZoneInfo("Europe/Kyiv")
SCHEDULES_DIR = config.BASE_DIR / "schedules"
SCHEDULES_DIR.mkdir(exist_ok=True)

DAYS_NAMES = [
    "Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота", "Неділя"
]


class ScheduleService:
    @classmethod
    def load_schedule_data(cls, group_name: str) -> dict | None:
        file_path = SCHEDULES_DIR / f"{group_name}.json"
        if not file_path.exists():
            return None
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ScheduleService] Error reading {file_path}: {e}")
            return None

    @classmethod
    def get_current_week(cls, ref_date_str: str, total_weeks: int = 1) -> int:
        if total_weeks <= 1:
            return 1
        try:
            ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d")
        except ValueError:
            return 1

        now = datetime.now(KYIV_TZ).replace(tzinfo=None)
        delta_days = (now - ref_date).days
        weeks_passed = delta_days // 7
        return (weeks_passed % total_weeks) + 1

    @classmethod
    def render_full_schedule(cls, group_name: str) -> str:
        data = cls.load_schedule_data(group_name)
        if not data:
            return f"> Розклад для групи **{group_name}** ще не додано в систему."

        weeks_list = data.get("schedule", [])
        total_weeks = len(weeks_list)

        if total_weeks == 0:
            return f"> Розклад для групи **{group_name}** порожній."

        time_slots = data.get("time", [])
        subjects = data.get("subjects", {})
        output = []

        current_week = 1
        if total_weeks > 1:
            current_week = cls.get_current_week(data.get("ref_date", "2026-09-01"), total_weeks)
            output.append(f"> **Поточний тиждень:** {current_week}-й\n")

        for w_idx, week_data in enumerate(weeks_list):
            week_num = w_idx + 1

            if total_weeks > 1:
                is_active = (week_num == current_week)
                active_badge = " ⭐ (Поточний)" if is_active else ""
                output.append(f"## Тиждень {week_num}{active_badge}")

            for day_num in range(1, 7):
                day_str = str(day_num)
                lessons_ids = week_data.get(day_str, [])

                if not any(lessons_ids):
                    continue

                day_header = "###" if total_weeks > 1 else "##"
                output.append(f"{day_header} {DAYS_NAMES[day_num - 1]}")
                output.append("| № | Час | Дисципліна | Викладач | Авд. | Посилання |")
                output.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

                for idx, sub_id in enumerate(lessons_ids, start=1):
                    time_str = time_slots[idx - 1] if idx - 1 < len(time_slots) else ""

                    if sub_id and sub_id in subjects:
                        row_str = cls.format_subject_row(idx, time_str, subjects[sub_id], sub_id)
                        output.append(row_str)
                    else:
                        output.append(f"| {idx} | {time_str} | — | — | — | — |")

                output.append("")

        return "\n".join(output)

    @classmethod
    def render_today(cls, group_name: str) -> str:
        data = cls.load_schedule_data(group_name)
        if not data:
            return f"> Розклад для групи **{group_name}** недоступний."

        now = datetime.now(KYIV_TZ)
        day_idx = now.weekday() + 1

        if day_idx > 6:
            return "> **Сьогодні вихідний день.**"

        weeks_list = data.get("schedule", [])
        total_weeks = len(weeks_list)

        if total_weeks == 0:
            return "> **Розклад порожній.**"

        current_week = cls.get_current_week(data.get("ref_date", "2026-09-01"), total_weeks) if total_weeks > 1 else 1
        week_data = weeks_list[current_week - 1] if current_week - 1 < len(weeks_list) else {}
        day_lessons = week_data.get(str(day_idx), [])
        time_slots = data.get("time", [])
        subjects = data.get("subjects", {})

        if not any(day_lessons):
            return f"> **Сьогодні ({DAYS_NAMES[day_idx - 1]}) пар немає.**"

        output = [
            f"### Розклад на сьогодні ({DAYS_NAMES[day_idx - 1]})",
            "| № | Час | Дисципліна | Викладач | Авд. | Посилання |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for idx, sub_id in enumerate(day_lessons, start=1):
            time_str = time_slots[idx - 1] if idx - 1 < len(time_slots) else ""
            if sub_id and sub_id in subjects:
                row_str = cls.format_subject_row(idx, time_str, subjects[sub_id], sub_id)
                output.append(row_str)

        return "\n".join(output)

    @staticmethod
    def format_subject_row(idx, time_str, sub: dict, default_name: str) -> str:
        name = sub.get("name", default_name)
        teacher = sub.get("lecturers_name", "—") or "—"
        aud = f"`{sub['room']}`" if sub.get("room") else "—"
        link = f"[Приєднатися]({sub['link']})" if sub.get("link") else "—"

        return f"| {idx} | {time_str} | **{name}** | {teacher} | {aud} | {link} |"

    @classmethod
    def render_full_template(cls, group_name: str) -> str:
        data = cls.load_schedule_data(group_name)
        if not data:
            return f"> Розклад для групи **{group_name}** ще не додано в систему."

        today_block = cls.render_today(group_name)
        full_block = cls.render_full_schedule(group_name)

        return f"""## Пари на сьогодні
{today_block}

---

## Повний розклад занять
{full_block}"""
