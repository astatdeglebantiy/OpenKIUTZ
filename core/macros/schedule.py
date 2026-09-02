from core.macros.base import BaseMacro
from core.schedule import ScheduleService, default_schedule_service


class ScheduleMacro(BaseMacro):
    def __init__(self, service: ScheduleService | None = None):
        self._service = service or default_schedule_service

    @property
    def name(self) -> str:
        return "schedule"

    def execute(self, arg: str) -> str:
        group_name = arg.strip().strip("'\"")
        return self._service.render_full_template(group_name)


class ScheduleTodayMacro(BaseMacro):
    def __init__(self, service: ScheduleService | None = None):
        self._service = service or default_schedule_service

    @property
    def name(self) -> str:
        return "schedule_today"

    def execute(self, arg: str) -> str:
        group_name = arg.strip().strip("'\"")
        return self._service.render_today(group_name)


class ScheduleFullMacro(BaseMacro):
    def __init__(self, service: ScheduleService | None = None):
        self._service = service or default_schedule_service

    @property
    def name(self) -> str:
        return "schedule_full"

    def execute(self, arg: str) -> str:
        group_name = arg.strip().strip("'\"")
        return self._service.render_full_schedule(group_name)
