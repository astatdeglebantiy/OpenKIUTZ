from pathlib import Path
import config
from core.models.academic import Specialty, Group


class AcademicRepository:
    def __init__(self, config_path: Path | None = None):
        self.config_path: Path = config_path or (config.BASE_DIR / "groups.yaml")
        self._specialties: list[Specialty] = []
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            return

        data = {}
        try:
            import yaml
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except (ImportError, ModuleNotFoundError):
            import json
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        except Exception as e:
            print(f"[AcademicRepository] Error loading {self.config_path}: {e}")
            data = {}

        self._specialties = []
        for spec_data in data.get("specialties", []):
            groups_list = []
            for grp_data in spec_data.get("groups", []):
                groups_list.append(
                    Group(
                        name=grp_data.get("name", ""),
                        slug_name=grp_data.get("slug_name", ""),
                        course=int(grp_data.get("course", 1)),
                        curator=grp_data.get("curator"),
                        headman=grp_data.get("headman"),
                        deputy_headman=grp_data.get("deputy_headman"),
                        moderators=grp_data.get("moderators"),
                        description=grp_data.get("description"),
                    )
                )

            self._specialties.append(
                Specialty(
                    code=str(spec_data.get("code", "")),
                    old_code=spec_data.get("old_code"),
                    name=spec_data.get("name", ""),
                    short_name=spec_data.get("short_name", ""),
                    groups=groups_list
                )
            )

    def get_all_specialties(self) -> list[Specialty]:
        return self._specialties

    def find_group(self, name: str) -> Group | None:
        for spec in self._specialties:
            found = spec.find_group(name)
            if found:
                return found
        return None


default_academic_repository = AcademicRepository()