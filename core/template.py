from pathlib import Path
import config


class TemplateEngine:
    def __init__(self, templates_dir: Path | None = None, site_title: str | None = None):
        self.templates_dir: Path = templates_dir or config.TEMPLATES_DIR
        self.site_title: str = site_title or config.SITE_TITLE
        self._cache: dict[str, str] = {}

    def get_template(self, name: str) -> str:
        if name in self._cache:
            return self._cache[name]

        template_file = self.templates_dir / name
        content = template_file.read_text(encoding="utf-8") if template_file.exists() else "{{CONTENT}}"
        self._cache[name] = content
        return content

    def clear_cache(self) -> None:
        self._cache.clear()

    def render(self, template_name: str, context: dict[str, str]) -> str:
        template = self.get_template(template_name)
        for key, val in context.items():
            template = template.replace(key, val)
        return template

    def render_layout(self, title: str, content_html: str, slug: str = "") -> str:
        raw_link = f'<a href="/raw/{slug}" class="site-raw-btn" target="_blank">Raw</a>' if slug and slug not in ("map", "search", "diff") else ""

        context = {
            "{{TITLE}}": title,
            "{{SITE_TITLE}}": self.site_title,
            "{{SLUG}}": slug,
            "{{RAW_LINK}}": raw_link,
            "{{CONTENT}}": content_html
        }

        return self.render("layout.html", context)

    def render_map_view(self, links_html: str) -> str:
        body = f"<h1>Site Map</h1><ul>{links_html or '<li>No posts available.</li>'}</ul>"
        return self.render_layout("Site Map", body, slug="map")

    def render_diff_view(self, status_raw: str, diff_html: str) -> str:
        template = self.get_template("diff.html")
        body = template.replace("{{STATUS}}", status_raw or "Working tree clean.").replace("{{DIFF_HTML}}", diff_html)
        return self.render_layout("Git Diff", body, slug="diff")

    def render_search_view(self, posts_list_html: str) -> str:
        template = self.get_template("search.html")
        body = template.replace("{{POSTS_LIST}}", posts_list_html or "<li>No pages found.</li>")
        return self.render_layout("Search", body, slug="search")


default_template_engine = TemplateEngine()
