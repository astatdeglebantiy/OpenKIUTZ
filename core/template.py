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

def render_search_view(posts_list_html: str) -> str:
    template = _read_template("search.html")
    body = template.replace("{{POSTS_LIST}}", posts_list_html or "<li>No pages found.</li>")
    return render_layout("Search", body, slug="search")

def render_diff_view(status_raw: str, diff_html: str) -> str:
    template = _read_template("diff.html")
    body = template.replace("{{STATUS}}", status_raw or "Working tree clean.").replace("{{DIFF_HTML}}", diff_html)
    return render_layout("Git Diff", body, slug="diff")

def render_map_view(links_html: str) -> str:
    body = f"<h1>Site Map</h1><ul>{links_html or '<li>No posts available.</li>'}</ul>"
    return render_layout("Site Map", body, slug="map")