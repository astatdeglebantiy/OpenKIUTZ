import datetime
import os
from pathlib import Path
from typing import Dict, List
import config


def get_inwards_routes(base_dir: Path | None = None) -> List[Dict[str, str]]:
    routes = []
    base_path = base_dir or config.POSTS_DIR

    if not base_path.exists():
        return routes

    for file_path in base_path.rglob("*.md"):
        rel_path = file_path.relative_to(base_path)
        slug = rel_path.with_suffix("").as_posix()

        if slug in ("index", "home"):
            loc = "/"
            priority = "1.0"
            changefreq = "daily"
        else:
            loc = f"/p/{slug}"
            if "news" in slug:
                priority = "0.8"
                changefreq = "weekly"
            else:
                priority = "0.9"
                changefreq = "weekly"

        mtime = os.path.getmtime(file_path)
        lastmod = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d")

        routes.append({
            "loc": loc,
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority
        })

    return routes


def generate_sitemap_xml() -> str:
    routes = get_inwards_routes()

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    has_root = any(r["loc"] == "/" for r in routes)
    if not has_root:
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        routes.insert(0, {
            "loc": "/",
            "lastmod": today,
            "changefreq": "daily",
            "priority": "1.0"
        })

    for item in routes:
        full_url = f"{config.BASE_URL}{item['loc']}"
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{full_url}</loc>")
        xml_lines.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{item['priority']}</priority>")
        xml_lines.append("  </url>")

    xml_lines.append("</urlset>")

    return "\n".join(xml_lines)