import re
from pathlib import Path
import config


class MarkdownParser:
    @staticmethod
    def parse_frontmatter(raw_text: str) -> tuple[dict, str]:
        metadata = {}
        content = raw_text

        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()
                content = parts[2].strip()

        return metadata, content

    @classmethod
    def resolve_includes(cls, text: str, current_dir: Path) -> str:
        def replace_include(match):
            rel_path = match.group(1).strip()
            target_file = (current_dir / rel_path).resolve()

            if not str(target_file).startswith(str(config.POSTS_DIR.resolve())) or not target_file.exists():
                return f'<div class="include-error">[Include error: {rel_path} not found]</div>'

            included_raw = target_file.read_text(encoding="utf-8")
            _, included_content = cls.parse_frontmatter(included_raw)
            return cls.resolve_includes(included_content, target_file.parent)

        return re.sub(r'@include\((.*?)\)', replace_include, text)

    @classmethod
    def to_html(cls, md_text: str, current_dir: Path = None) -> str:
        if current_dir is None:
            current_dir = config.POSTS_DIR

        text = cls.resolve_includes(md_text, current_dir)

        code_blocks = []

        def stash_code_block(m):
            lang = m.group(1) or ""
            code = m.group(2)
            escaped = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_blocks.append(f'<pre><code class="language-{lang}">{escaped}</code></pre>')
            return f"<!--CODE_BLOCK_{len(code_blocks) - 1}-->"

        text = re.sub(r'```(\w+)?\n([\s\S]*?)```', stash_code_block, text)

        raw_tags = []

        def stash_raw_tag(m):
            raw_tags.append(m.group(0))
            return f"<!--RAW_TAG_{len(raw_tags) - 1}-->"

        text = re.sub(r'<(script|style)\b[^>]*>[\s\S]*?<\/\1>', stash_raw_tag, text, flags=re.IGNORECASE)

        lines = text.splitlines()
        processed = []

        in_ul = False
        in_ol = False
        in_quote = False
        in_table = False
        table_rows = []

        def close_open_containers():
            nonlocal in_ul, in_ol, in_quote, in_table, table_rows
            res = []
            if in_ul:
                res.append("</ul>")
                in_ul = False
            if in_ol:
                res.append("</ol>")
                in_ol = False
            if in_quote:
                res.append("</blockquote>")
                in_quote = False
            if in_table:
                res.append(cls._render_table(table_rows))
                table_rows = []
                in_table = False
            return res

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("|") and stripped.endswith("|"):
                if in_ul or in_ol or in_quote:
                    processed.extend(close_open_containers())
                in_table = True
                table_rows.append(stripped)
                continue
            elif in_table:
                processed.extend(close_open_containers())

            if re.match(r'^(\-{3,}|\*{3,}|_{3,})$', stripped):
                processed.extend(close_open_containers())
                processed.append("<hr>")
                continue

            h_match = re.match(r'^(#{1,6})\s+(.*)$', line)
            if h_match:
                processed.extend(close_open_containers())
                lvl = len(h_match.group(1))
                processed.append(f"<h{lvl}>{h_match.group(2)}</h{lvl}>")
                continue

            if line.startswith("> "):
                if in_ul or in_ol:
                    processed.extend(close_open_containers())
                if not in_quote:
                    processed.append("<blockquote>")
                    in_quote = True
                processed.append(f"<p>{line[2:]}</p>")
                continue
            elif in_quote:
                processed.append("</blockquote>")
                in_quote = False

            task_match = re.match(r'^[\*\-]\s+\[([ xX])\]\s+(.*)$', stripped)
            if task_match:
                if in_ol: processed.extend(close_open_containers())
                if not in_ul:
                    processed.append('<ul class="task-list">')
                    in_ul = True
                checked = 'checked disabled' if task_match.group(1).lower() == 'x' else 'disabled'
                processed.append(f'<li class="task-item"><input type="checkbox" {checked}> {task_match.group(2)}</li>')
                continue

            ul_match = re.match(r'^[\*\-]\s+(.*)$', stripped)
            if ul_match:
                if in_ol: processed.extend(close_open_containers())
                if not in_ul:
                    processed.append("<ul>")
                    in_ul = True
                processed.append(f"<li>{ul_match.group(1)}</li>")
                continue

            ol_match = re.match(r'^\d+\.\s+(.*)$', stripped)
            if ol_match:
                if in_ul: processed.extend(close_open_containers())
                if not in_ol:
                    processed.append("<ol>")
                    in_ol = True
                processed.append(f"<li>{ol_match.group(1)}</li>")
                continue

            if in_ul or in_ol:
                processed.extend(close_open_containers())

            if not stripped:
                processed.append("")
                continue

            if (stripped.startswith("<") and stripped.endswith(">")) or stripped.startswith("<!--"):
                processed.append(line)
            else:
                processed.append(f"<p>{line}</p>")

        processed.extend(close_open_containers())
        html = "\n".join(processed)

        html = re.sub(r'~~(.*?)~~', r'<del>\1</del>', html)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
        html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

        for idx, block in enumerate(code_blocks):
            html = html.replace(f"<!--CODE_BLOCK_{idx}-->", block)

        for idx, tag in enumerate(raw_tags):
            html = html.replace(f"<!--RAW_TAG_{idx}-->", tag)

        return html

    @classmethod
    def _render_table(cls, rows: list[str]) -> str:
        if len(rows) < 2:
            return "\n".join(rows)

        def split_row(r):
            return [c.strip() for c in r.strip("|").split("|")]

        header_cols = split_row(rows[0])
        body_start = 2 if re.match(r'^[\s\|:\-]+$', rows[1]) else 1

        th_html = "".join([f"<th>{col}</th>" for col in header_cols])
        thead = f"<thead><tr>{th_html}</tr></thead>"

        tbody_rows = []
        for r in rows[body_start:]:
            cols = split_row(r)
            tds = "".join([f"<td>{c}</td>" for c in cols])
            tbody_rows.append(f"<tr>{tds}</tr>")

        tbody = f"<tbody>{''.join(tbody_rows)}</tbody>"
        return f"<table>{thead}{tbody}</table>"
