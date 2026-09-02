from dataclasses import dataclass, field
from core.models.academic.group import Group


@dataclass
class Specialty:
    code: str
    name: str
    short_name: str
    old_code: str | int | None = None
    groups: list[Group] = field(default_factory=list)

    def find_group(self, slug_name: str) -> Group | None:
        for group in self.groups:
            if group.slug_name.lower() == slug_name.lower():
                return group
        return None
