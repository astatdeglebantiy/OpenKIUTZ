import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

import config
from core.git_sync import GitService
from core.parser import MarkdownParser
from core.template import render_layout, render_search_view, render_diff_view, render_map_view

SSE_CLIENTS = []
SSE_LOCK = threading.Lock()

def broadcast_live_update(slug: str):
    message = f"data: {json.dumps({'event': 'update', 'slug': slug})}\n\n".encode("utf-8")
    dead_clients = []

    with SSE_LOCK:
        for client_wfile in SSE_CLIENTS:
            try:
                client_wfile.write(message)
                client_wfile.flush()
            except Exception:
                dead_clients.append(client_wfile)

        for dead in dead_clients:
            if dead in SSE_CLIENTS:
                SSE_CLIENTS.remove(dead)


class SiteRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")

        # Favicon
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

        # SSE Live Reload Stream
        if path == "api/live":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            with SSE_LOCK:
                SSE_CLIENTS.append(self.wfile)

            try:
                while True:
                    import time
                    time.sleep(30)
                    with SSE_LOCK:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except Exception:
                with SSE_LOCK:
                    if self.wfile in SSE_CLIENTS:
                        SSE_CLIENTS.remove(self.wfile)
            return

        # JSON API
        if path == "api/posts":
            posts_data = []
            for f in sorted(config.POSTS_DIR.rglob("*.md")):
                slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                try:
                    raw = f.read_text(encoding="utf-8")
                    meta, _ = MarkdownParser.parse_frontmatter(raw)
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

        if path.startswith("api/posts/"):
            slug = path.replace("api/posts/", "", 1).rstrip("/")
            file_path = (config.POSTS_DIR / f"{slug}.md").resolve()

            if not file_path.exists():
                file_path = (config.POSTS_DIR / slug / "index.md").resolve()

            if not self._is_safe_path(config.POSTS_DIR, file_path):
                self._send_json({"error": "Post not found"}, 404)
                return

            raw = file_path.read_text(encoding="utf-8")
            meta, content = MarkdownParser.parse_frontmatter(raw)
            html_content = MarkdownParser.to_html(content, current_dir=file_path.parent)

            self._send_json({
                "slug": slug,
                "title": meta.get("title", slug),
                "meta": meta,
                "markdown": content,
                "html": html_content
            })
            return

        # Static
        if path.startswith("static/"):
            file_path = (config.STATIC_DIR / path.replace("static/", "", 1)).resolve()
            if self._is_safe_path(config.STATIC_DIR, file_path):
                self._serve_file(file_path)
                return
            self.send_error(404, "Static file not found")
            return

        # Resources
        if path.startswith("resources/"):
            file_path = (config.RESOURCES_DIR / path.replace("resources/", "", 1)).resolve()
            if self._is_safe_path(config.RESOURCES_DIR, file_path):
                self._serve_file(file_path)
                return
            self.send_error(404, "Resource not found")
            return

        # Raw MD
        if path.startswith("raw/"):
            slug = path.split("raw/", 1)[1].rstrip("/")
            if slug.endswith(".md"):
                slug = slug[:-3]

            file_path = (config.POSTS_DIR / f"{slug}.md").resolve()
            if not file_path.exists():
                file_path = (config.POSTS_DIR / slug / "index.md").resolve()

            if not self._is_safe_path(config.POSTS_DIR, file_path):
                self.send_error(404, f"File '{slug}' not found")
                return

            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        # / >>>>> Main Page
        if path == "":
            self.send_response(302)
            self.send_header("Location", f"/p/{config.DEFAULT_PAGE}")
            self.end_headers()
            return

        # Map
        if path in ("map", "sitemap"):
            posts = [f.relative_to(config.POSTS_DIR).with_suffix("").as_posix() for f in sorted(config.POSTS_DIR.rglob("*.md"))]
            links = "".join([f'<li><a href="/p/{p}">{p}</a></li>' for p in posts])
            self._send_html(render_map_view(links))
            return

        # Search
        if path in ("search", "p/search"):
            posts_html = []
            for f in sorted(config.POSTS_DIR.rglob("*.md")):
                rel_slug = f.relative_to(config.POSTS_DIR).with_suffix("").as_posix()
                try:
                    raw = f.read_text(encoding="utf-8")
                    meta, _ = MarkdownParser.parse_frontmatter(raw)
                    title = meta.get("title", rel_slug)
                    posts_html.append(f'<li class="search-item" style="margin: 8px 0;"><a href="/p/{rel_slug}"><b>{title}</b></a> <code style="margin-left: 8px;">{rel_slug}</code></li>')
                except Exception:
                    pass

            self._send_html(render_search_view("".join(posts_html)))
            return

        # Git Diff
        if path in ("diff", "git"):
            status_raw = GitService.status()
            diff_raw = GitService.diff()

            escaped_diff = diff_raw.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            highlighted_lines = []
            for line in escaped_diff.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    highlighted_lines.append(f'<span style="color: #7ee787;">{line}</span>')
                elif line.startswith("-") and not line.startswith("---"):
                    highlighted_lines.append(f'<span style="color: #ffa198;">{line}</span>')
                elif line.startswith("@@"):
                    highlighted_lines.append(f'<span style="color: #79c0ff;">{line}</span>')
                else:
                    highlighted_lines.append(line)

            self._send_html(render_diff_view(status_raw, "\n".join(highlighted_lines)))
            return

        # Pages
        if path.startswith("p/"):
            slug = path.split("p/", 1)[1].rstrip("/")
            file_path = (config.POSTS_DIR / f"{slug}.md").resolve()

            if not file_path.exists():
                file_path = (config.POSTS_DIR / slug / "index.md").resolve()

            if not self._is_safe_path(config.POSTS_DIR, file_path):
                self.send_error(404, f"Page '{slug}' not found")
                return

            raw = file_path.read_text(encoding="utf-8")
            meta, content = MarkdownParser.parse_frontmatter(raw)
            html_content = MarkdownParser.to_html(content, current_dir=file_path.parent)
            title = meta.get("title", slug)

            self._send_html(render_layout(title, html_content, slug=slug))
            return

        self.send_error(404, "Not Found")

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

    def _is_safe_path(self, base_dir: Path, target_path: Path) -> bool:
        return str(target_path).startswith(str(base_dir.resolve())) and target_path.exists() and target_path.is_file()

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
