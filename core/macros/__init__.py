from core.macros.base import BaseMacro, MacroRegistry
from core.macros.common import CountMacro, BadgeMacro, ListMacro, DateMacro
from core.macros.groups import GroupsCatalogMacro, GroupInfoMacro
from core.macros.schedule import ScheduleMacro, ScheduleTodayMacro, ScheduleFullMacro


def create_default_registry() -> MacroRegistry:
    registry = MacroRegistry()

    count_macro = CountMacro()

    registry.register(count_macro)
    registry.register(BadgeMacro(count_macro=count_macro))
    registry.register(ListMacro())
    registry.register(DateMacro())

    registry.register(GroupsCatalogMacro())
    registry.register(GroupInfoMacro())

    registry.register(ScheduleMacro())
    registry.register(ScheduleTodayMacro())
    registry.register(ScheduleFullMacro())

    return registry


default_macro_registry = create_default_registry()
