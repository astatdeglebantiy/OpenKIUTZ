import re
from pathlib import Path
import config
from core.macros import MacroRegistry, default_macro_registry
from core.rules import (
    ParsingContext,
    BaseBlockRule,
    TableRule,
    HorizontalRule,
    HeadingRule,
    BlockquoteRule,
    TaskListRule,
    UnorderedListRule,
    OrderedListRule,
    EmptyLineRule,
    RawHtmlRule,
    ParagraphRule,
)


class MarkdownParser:
    def __init__(self, macro_registry: MacroRegistry | None = None):
        self.macro_registry = macro_registry or default_macro_registry
        self.rules: list[BaseBlockRule] = [
            TableRule(),
            HorizontalRule(),
            HeadingRule(),
            BlockquoteRule(),
            TaskListRule(),
            UnorderedListRule(),
            OrderedListRule(),
            EmptyLineRule(),
            RawHtmlRule(),
            ParagraphRule(),
        ]

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

    def resolve_includes(self, text: str, current_dir: Path) -> str:
        def replace_include(match):
            rel_path = match.group(1).strip()
            target_file = (current_dir / rel_path).resolve()

            if not str(target_file).startswith(str(config.POSTS_DIR.resolve())) or not target_file.exists():
                return f'<div class="include-error">[Include error: {rel_path} not found]</div>'

            included_raw = target_file.read_text(encoding="utf-8")
            _, included_content = self.parse_frontmatter(included_raw)
            return self.resolve_includes(included_content, target_file.parent)

        return re.sub(r'@include\((.*?)\)', replace_include, text)

    def resolve_macros(self, text: str) -> str:
        def replace_fn(match):
            fn_name = match.group(1)
            raw_arg = match.group(2)
            return self.macro_registry.execute(fn_name, raw_arg)

        return re.sub(r'@([a-zA-Z_]\w*)\((.*?)\)', replace_fn, text)

    @staticmethod
    def _stash_code_blocks(text: str, stash: list[str]) -> str:
        def stash_cb(m):
            lang = m.group(1) or ""
            code = m.group(2).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            stash.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            return f"<!--CODE_BLOCK_{len(stash)-1}-->"

        return re.sub(r'```(\w+)?\n([\s\S]*?)```', stash_cb, text)

    @staticmethod
    def _stash_raw_tags(text: str, stash: list[str]) -> str:
        def stash_tag(m):
            stash.append(m.group(0))
            return f"<!--RAW_TAG_{len(stash)-1}-->"

        return re.sub(r'<(script|style)\b[^>]*>[\s\S]*?<\/\1>', stash_tag, text, flags=re.IGNORECASE)

    @staticmethod
    def _apply_inline_formatting(html: str) -> str:
        html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)

        html = re.sub(r'~~(.*?)~~', r'<del>\1</del>', html)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'(?<!\w)__(.*?)__(?!\w)', r'<strong>\1</strong>', html)

        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', html)

        return html

    def to_html(self, md_text: str, current_dir: Path | None = None) -> str:
        if current_dir is None:
            current_dir = config.POSTS_DIR

        text = self.resolve_includes(md_text, current_dir)
        text = self.resolve_macros(text)

        code_blocks: list[str] = []
        text = self._stash_code_blocks(text, code_blocks)

        raw_tags: list[str] = []
        text = self._stash_raw_tags(text, raw_tags)

        ctx = ParsingContext()
        for line in text.splitlines():
            stripped = line.strip()
            for rule in self.rules:
                if rule.matches(line, stripped, ctx):
                    rule.process(line, stripped, ctx)
                    break

        ctx.close_containers()
        html = "\n".join(ctx.processed)
        html = self._apply_inline_formatting(html)

        for idx, block in enumerate(code_blocks):
            html = html.replace(f"<!--CODE_BLOCK_{idx}-->", block)

        for idx, tag in enumerate(raw_tags):
            html = html.replace(f"<!--RAW_TAG_{idx}-->", tag)

        return html
