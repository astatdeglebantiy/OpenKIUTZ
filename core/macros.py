import config
from datetime import datetime

from core.schedule import ScheduleService


def macro_count(prefix: str) -> str:
    prefix = prefix.strip().strip("'\"")
    posts = [f.relative_to(config.POSTS_DIR).as_posix() for f in config.POSTS_DIR.rglob("*.md")]

    unique = set(
        p.replace(prefix, "", 1).strip("/").split("/")[0]
        for p in posts if p.startswith(prefix)
    )
    unique.discard("")
    return str(len(unique))


def macro_badge(prefix: str) -> str:
    count = macro_count(prefix)
    return f'<span class="badge">{count}</span>'


def macro_list(prefix: str) -> str:
    prefix = prefix.strip().strip("'\"")
    items = []

    for f in sorted(config.POSTS_DIR.glob(f"{prefix}*.md")):
        slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
        name = f.stem
        items.append(f'<li><a href="/p/{slug}">{name}</a></li>')

    return f'<ul>{"".join(items) or "<li>Порожньо</li>"}</ul>'


def macro_date(fmt: str = "%d.%m.%Y") -> str:
    fmt = fmt.strip().strip("'\"") or "%d.%m.%Y"
    return datetime.now().strftime(fmt)

def macro_schedule(group_name: str) -> str:
    return ScheduleService.render_full_schedule(group_name.strip().strip("'\""))

def macro_schedule_today(group_name: str) -> str:
    return ScheduleService.render_today(group_name.strip().strip("'\""))

def macro_schedule_full(group_name: str) -> str:
    return ScheduleService.render_full_schedule(group_name.strip().strip("'\""))


MACROS = {
    "count": macro_count,
    "badge": macro_badge,
    "list": macro_list,
    "date": macro_date,
    "schedule": macro_schedule,
    "schedule_today": macro_schedule_today,
    "schedule_full": macro_schedule_full,
}