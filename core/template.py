import config

def _read_template(name: str) -> str:
    template_file = config.TEMPLATES_DIR / name
    if template_file.exists():
        return template_file.read_text(encoding="utf-8")
    return "{{CONTENT}}"

def render_layout(title: str, content_html: str, slug: str = "") -> str:
    raw_link = f'<a href="/raw/{slug}" class="site-raw-btn" target="_blank">Raw</a>' if slug and slug not in ("map", "search", "diff") else ""
    template = _read_template("layout.html")

    replacements = {
        "{{TITLE}}": title,
        "{{SITE_TITLE}}": config.SITE_TITLE,
        "{{SLUG}}": slug,
        "{{RAW_LINK}}": raw_link,
        "{{CONTENT}}": content_html
    }

    for key, val in replacements.items():
        template = template.replace(key, val)

    return template

def render_map_view(links_html: str) -> str:
    body = f"<h1>Site Map</h1><ul>{links_html or '<li>No posts available.</li>'}</ul>"
    return render_layout("Site Map", body, slug="map")