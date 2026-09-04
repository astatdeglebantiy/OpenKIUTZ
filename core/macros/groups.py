from core.academic import AcademicRepository, default_academic_repository
from core.macros.base import BaseMacro


class GroupsCatalogMacro(BaseMacro):
    def __init__(self, repository: AcademicRepository | None = None):
        self._repository = repository or default_academic_repository

    @property
    def name(self) -> str:
        return "groups_catalog"

    def execute(self, arg: str) -> str:
        specialties = self._repository.get_all_specialties()
        if not specialties:
            return "> Список груп порожній або ще заповнюється."

        output = []
        for spec in specialties:
            code_str = f" ({spec.short_name} · {spec.code})" if spec.short_name else f" ({spec.code})"
            output.append(f"## {spec.name}{code_str}\n")

            if not spec.groups:
                output.append("> У цій спеціальності поки немає доданих груп.\n")
                continue

            for grp in spec.groups:
                output.append(f"### [{grp.name}](/p/{grp.slug})")

                details = []
                if grp.course:
                    details.append(f"**Курс:** {grp.course}")
                if grp.curator:
                    details.append(f"**Куратор:** {grp.curator}")
                if grp.headman:
                    headman_link = f"[{grp.headman}](https://t.me/{grp.headman.lstrip('@')})" if grp.headman.startswith("@") else grp.headman
                    details.append(f"**Староста:** {headman_link}")

                if details:
                    output.append(" · ".join(details))

                if grp.description:
                    output.append(f"\n{grp.description}")

                output.append("")

        return "\n".join(output)


class GroupInfoMacro(BaseMacro):
    def __init__(self, repository: AcademicRepository | None = None):
        self._repository = repository or default_academic_repository

    @property
    def name(self) -> str:
        return "group_info"

    def execute(self, arg: str) -> str:
        group_name = arg.strip().strip("'\"")
        group = self._repository.find_group(group_name)
        if not group:
            return f"> Інформація про групу **{group_name}** відсутня."

        output = []
        if group.course:
            output.append(f"* **Курс:** {group.course}")
        if group.curator:
            output.append(f"* **Куратор:** {group.curator}")
        if group.headman:
            headman_link = f"[{group.headman}](https://t.me/{group.headman.lstrip('@')})" if group.headman.startswith("@") else group.headman
            output.append(f"* **Староста:** {headman_link}")
        if group.deputy_headman:
            deputy_headman_link = f"[{group.deputy_headman}](https://t.me/{group.deputy_headman.lstrip('@')})" if group.deputy_headman.startswith("@") else group.deputy_headman
            output.append(f"* **Заступник старости:** {deputy_headman_link}")
        if group.moderators:
            mod_links = [
                f"[{m}](https://t.me/{m.lstrip('@')})" if m.startswith("@") else m
                for m in group.moderators
            ]
            output.append(f"* **Модератори:** {', '.join(mod_links)}")

        return "\n".join(output)
