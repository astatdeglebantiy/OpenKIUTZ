import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

def load_env(filepath: Path) -> None:
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip("'\""))

load_env(BASE_DIR / ".env")

POSTS_DIR = BASE_DIR / "inwards"
STATIC_DIR = BASE_DIR / "static"
RESOURCES_DIR = BASE_DIR / "resources"
TEMPLATES_DIR = BASE_DIR / "templates"

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "3000"))
SITE_TITLE = os.getenv("SITE_TITLE", "Markdown Site")
DEFAULT_PAGE = os.getenv("DEFAULT_PAGE", "index")

POSTS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
RESOURCES_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)