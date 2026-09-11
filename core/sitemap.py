import os
import datetime
from pathlib import Path
from typing import List, Dict


def get_inwards_routes(inwards_dir: str = "inwards") -> List[Dict[str, str]]:
    routes = []
    base_path = Path(inwards_dir)

    if not base_path.exists():
        return routes

    for file_path in base_path.rglob("*.md"):
        rel_path = file_path.relative_to(base_path)

        parts = list(rel_path.parts)

        parts[-1] = file_path.stem

        if parts == ["index"] or parts == ["home"]:
            url_path = ""
            priority = "1.0"
            changefreq = "daily"
        else:
            if parts[-1] == "index":
                parts.pop()
            url_path = "/".join(parts)

            if "news" in parts:
                priority = "0.8"
                changefreq = "weekly"
            else:
                priority = "0.9"
                changefreq = "weekly"

        mtime = os.path.getmtime(file_path)
        lastmod = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%d")

        routes.append({
            "loc": f"/{url_path}".rstrip("/") if url_path else "/",
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority
        })

    return routes


def generate_sitemap_xml(base_url: str = "https://kiutz.pp.ua", inwards_dir: str = "inwards") -> str:
    base_url = base_url.rstrip("/")
    routes = get_inwards_routes(inwards_dir)

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
        full_url = f"{base_url}{item['loc']}"
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{full_url}</loc>")
        xml_lines.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{item['priority']}</priority>")
        xml_lines.append("  </url>")

    xml_lines.append("</urlset>")

    return "\n".join(xml_lines)
