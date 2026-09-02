from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseMacro(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, arg: str) -> str:
        pass

    @staticmethod
    def get_prefix(arg: str) -> str:
        return arg.strip().strip("'\"")


class MacroRegistry:
    def __init__(self):
        self._macros: Dict[str, BaseMacro] = {}

    def register(self, macro: BaseMacro) -> "MacroRegistry":
        self._macros[macro.name] = macro
        return self

    def get(self, name: str) -> Optional[BaseMacro]:
        return self._macros.get(name)

    def execute(self, name: str, arg: str) -> str:
        macro = self.get(name)
        if not macro:
            return f"@{name}({arg})"
        try:
            return str(macro.execute(arg))
        except Exception as e:
            return f'<span style="color:red;">[Macro Error ({name}): {e}]</span>'
