from datetime import datetime
import config
from core.macros.base import BaseMacro


class CountMacro(BaseMacro):
    @property
    def name(self) -> str:
        return "count"

    def execute(self, arg: str) -> str:
        prefix = self.get_prefix(arg)
        posts = [f.relative_to(config.POSTS_DIR).as_posix() for f in config.POSTS_DIR.rglob("*.md")]

        unique = set(
            p.replace(prefix, "", 1).strip("/").split("/")[0]
            for p in posts if p.startswith(prefix)
        )
        unique.discard("")
        return str(len(unique))


class BadgeMacro(BaseMacro):
    def __init__(self, count_macro: CountMacro):
        self._count_macro = count_macro

    @property
    def name(self) -> str:
        return "badge"

    def execute(self, arg: str) -> str:
        count = self._count_macro.execute(arg)
        return f'<span class="badge">{count}</span>'


class ListMacro(BaseMacro):
    @property
    def name(self) -> str:
        return "list"

    def execute(self, arg: str) -> str:
        prefix = self.get_prefix(arg)
        items = []

        for f in sorted(config.POSTS_DIR.glob(f"{prefix}*.md"), key=str):
            slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
            name = f.stem
            items.append(f'<li><a href="/p/{slug}">{name}</a></li>')

        return f'<ul>{"".join(items) or "<li>Порожньо</li>"}</ul>'


class DateMacro(BaseMacro):
    @property
    def name(self) -> str:
        return "date"

    def execute(self, arg: str) -> str:
        fmt = arg.strip().strip("'\"") or "%d.%m.%Y"
        return datetime.now().strftime(fmt)
