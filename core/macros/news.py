from pathlib import Path
import config
from core.macros.base import BaseMacro


class NewsListMacro(BaseMacro):
    @property
    def name(self) -> str:
        return "news_list"

    @staticmethod
    def _parse_frontmatter(raw_text: str) -> dict:
        metadata = {}
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip().strip("'\"")
        return metadata

    def execute(self, arg: str) -> str:
        news_dir = config.POSTS_DIR / "news"
        if not news_dir.exists():
            return "> Новин поки немає."

        limit = int(arg.strip()) if arg.strip().isdigit() else None
        articles = []

        for f in sorted(news_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                raw = f.read_text(encoding="utf-8")
                meta = self._parse_frontmatter(raw)
                slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                articles.append({
                    "title": meta.get("title", f.stem),
                    "slug": slug,
                    "date": meta.get("date", ""),
                    "desc": meta.get("description", "")
                })
            except Exception:
                pass

        if not articles:
            return "> Новин поки немає."

        if limit:
            articles = articles[:limit]

        output = ['<div class="news-list">']
        for art in articles:
            date_html = f'<span class="news-date">{art["date"]}</span>' if art["date"] else ""
            desc_html = f'<p class="news-desc">{art["desc"]}</p>' if art["desc"] else ""
            output.append(
                f'<a href="/p/{art["slug"]}" class="news-card">'
                f'<div class="news-card-header">'
                f'<span class="news-title">{art["title"]}</span>'
                f'{date_html}'
                f'</div>'
                f'{desc_html}'
                f'</a>'
            )
        output.append('</div>')

        return "\n".join(output)
