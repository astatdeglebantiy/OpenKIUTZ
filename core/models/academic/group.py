from dataclasses import dataclass, field
from typing import List


@dataclass
class Group:
    name: str
    slug_name: str
    course: int
    curator: str | None = None
    headman: str | None = None
    deputy_headman: str | None = None
    moderators: List[str] | None = None
    description: str | None = None

    @property
    def slug(self) -> str:
        return f"specialtys_and_groups/{self.slug_name}"
