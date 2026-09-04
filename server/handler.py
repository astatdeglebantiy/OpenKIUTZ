import json
import mimetypes
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import config
from core.parser import MarkdownParser
from core.template import default_template_engine

markdown_parser = MarkdownParser()


class SiteRequestHandler(BaseHTTPRequestHandler):
    @staticmethod
    def _is_safe_path(base_dir: Path, target_path: Path) -> bool:
        return str(target_path).startswith(str(base_dir.resolve())) and target_path.exists() and target_path.is_file()

    def _resolve_post_file(self, slug: str) -> Path | None:
        slug = slug.strip("/")
        if slug.endswith(".md"):
            slug = slug[:-3]

        file_path = (config.POSTS_DIR / f"{slug}.md").resolve()
        if not file_path.exists():
            file_path = (config.POSTS_DIR / slug / "index.md").resolve()

        if not self._is_safe_path(config.POSTS_DIR, file_path):
            return None

        return file_path

    def _serve_file(self, file_path: Path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html: str, code: int = 200):
        data = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, data: dict, code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")

        if path == "favicon.ico":
            favicon_path = config.STATIC_DIR / "favicon.ico"
            if favicon_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
                self.send_header("Content-Length", str(favicon_path.stat().st_size))
                self.end_headers()
                self.wfile.write(favicon_path.read_bytes())
            else:
                self.send_response(204)
                self.end_headers()
            return

        if path == "api/posts":
            posts_data = []
            md_files: list[Path] = sorted(config.POSTS_DIR.rglob("*.md"))

            for f in md_files:
                slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                try:
                    raw = f.read_text(encoding="utf-8")
                    meta, _ = markdown_parser.parse_frontmatter(raw)
                    posts_data.append({
                        "slug": slug,
                        "title": meta.get("title", slug),
                        "meta": meta,
                        "url": f"/p/{slug}"
                    })
                except Exception:
                    pass
            self._send_json({"posts": posts_data})
            return

        if path == "api/search-dropdown":
            query_params = parse_qs(urlparse(self.path).query)
            query = query_params.get("q", [""])[0].lower().strip()

            if not query:
                self._send_html("")
                return

            matched = []
            for f in sorted(config.POSTS_DIR.rglob("*.md"), key=str):
                slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                try:
                    raw = f.read_text(encoding="utf-8")
                    meta, _ = markdown_parser.parse_frontmatter(raw)
                    title = meta.get("title", slug)

                    if query in title.lower() or query in slug.lower():
                        matched.append(
                            f'<a href="/p/{slug}" class="dropdown-item">'
                            f'<span class="dropdown-title">{title}</span>'
                            f'<span class="dropdown-slug">{slug}</span>'
                            f'</a>'
                        )
                except Exception:
                    pass

            result_html = "".join(matched[:6]) if matched else '<div class="dropdown-empty">Нічого не знайдено</div>'
            self._send_html(result_html)
            return

        if path.startswith("static/"):
            file_path = (config.STATIC_DIR / path.replace("static/", "", 1)).resolve()
            if self._is_safe_path(config.STATIC_DIR, file_path):
                self._serve_file(file_path)
                return
            self.send_error(404, "Static file not found")
            return

        if path.startswith("resources/"):
            file_path = (config.RESOURCES_DIR / path.replace("resources/", "", 1)).resolve()
            if self._is_safe_path(config.RESOURCES_DIR, file_path):
                self._serve_file(file_path)
                return
            self.send_error(404, "Resource not found")
            return

        if path.startswith("raw/"):
            slug = path.split("raw/", 1)[1]
            file_path = self._resolve_post_file(slug)
            if not file_path:
                self.send_error(404, f"File '{slug}' not found")
                return

            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "":
            self.send_response(302)
            self.send_header("Location", f"/p/{config.DEFAULT_PAGE}")
            self.end_headers()
            return

        if path in ("map", "sitemap"):
            posts = [f.relative_to(config.POSTS_DIR).with_suffix("").as_posix() for f in sorted(config.POSTS_DIR.rglob("*.md"))]
            links = "".join(f'<li><a href="/p/{p}">{p}</a></li>' for p in posts)
            self._send_html(default_template_engine.render_map_view(links))
            return

        if path.startswith("p/"):
            slug = path.split("p/", 1)[1]
            file_path = self._resolve_post_file(slug)
            if not file_path:
                self.send_error(404, f"Page '{slug}' not found")
                return

            raw = file_path.read_text(encoding="utf-8")
            meta, content = markdown_parser.parse_frontmatter(raw)
            html_content = markdown_parser.to_html(content, current_dir=file_path.parent)
            title = meta.get("title", slug)

            self._send_html(default_template_engine.render_layout(title, html_content, slug=slug))
            return

        self.send_error(404, "Not Found")
