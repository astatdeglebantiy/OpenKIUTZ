from abc import ABC, abstractmethod
import re


class ParsingContext:
    def __init__(self):
        self.in_ul: bool = False
        self.in_ol: bool = False
        self.in_quote: bool = False
        self.in_table: bool = False
        self.table_rows: list[str] = []
        self.processed: list[str] = []

    def close_containers(self) -> None:
        if self.in_ul:
            self.processed.append("</ul>")
            self.in_ul = False
        if self.in_ol:
            self.processed.append("</ol>")
            self.in_ol = False
        if self.in_quote:
            self.processed.append("</blockquote>")
            self.in_quote = False
        if self.in_table:
            self.processed.append(self._render_table(self.table_rows))
            self.table_rows = []
            self.in_table = False

    @staticmethod
    def _render_table(rows: list[str]) -> str:
        if len(rows) < 2:
            return "\n".join(rows)

        def split_row(r: str) -> list[str]:
            return [c.strip() for c in r.strip("|").split("|")]

        header_cols = split_row(rows[0])
        body_start = 2 if re.match(r'^[\s\|:\-]+$', rows[1]) else 1

        th_html = "".join(f"<th>{col}</th>" for col in header_cols)
        thead = f"<thead><tr>{th_html}</tr></thead>"

        tbody_rows = []
        for r in rows[body_start:]:
            cols = split_row(r)
            tds = "".join(f"<td>{c}</td>" for c in cols)
            tbody_rows.append(f"<tr>{tds}</tr>")

        tbody = f"<tbody>{''.join(tbody_rows)}</tbody>"
        return f"<table>{thead}{tbody}</table>"


class BaseBlockRule(ABC):
    @abstractmethod
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        pass

    @abstractmethod
    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        pass


class TableRule(BaseBlockRule):
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return stripped.startswith("|") and stripped.endswith("|")

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        if ctx.in_ul or ctx.in_ol or ctx.in_quote:
            ctx.close_containers()
        ctx.in_table = True
        ctx.table_rows.append(stripped)


class HorizontalRule(BaseBlockRule):
    PATTERN = re.compile(r'^(\-{3,}|\*{3,}|_{3,})$')

    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return bool(self.PATTERN.match(stripped))

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        ctx.close_containers()
        ctx.processed.append("<hr>")


class HeadingRule(BaseBlockRule):
    PATTERN = re.compile(r'^(#{1,6})\s+(.*)$')

    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return bool(self.PATTERN.match(line))

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        ctx.close_containers()
        match = self.PATTERN.match(line)
        if match:
            level = len(match.group(1))
            ctx.processed.append(f"<h{level}>{match.group(2)}</h{level}>")


class BlockquoteRule(BaseBlockRule):
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return line.startswith("> ")

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        if ctx.in_ul or ctx.in_ol or ctx.in_table:
            ctx.close_containers()
        if not ctx.in_quote:
            ctx.processed.append("<blockquote>")
            ctx.in_quote = True
        ctx.processed.append(f"<p>{line[2:]}</p>")


class TaskListRule(BaseBlockRule):
    PATTERN = re.compile(r'^[\*\-]\s+\[([ xX])\]\s+(.*)$')

    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return bool(self.PATTERN.match(stripped))

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        if ctx.in_ol or ctx.in_quote or ctx.in_table:
            ctx.close_containers()
        if not ctx.in_ul:
            ctx.processed.append('<ul class="task-list">')
            ctx.in_ul = True
        match = self.PATTERN.match(stripped)
        if match:
            checked = 'checked disabled' if match.group(1).lower() == 'x' else 'disabled'
            ctx.processed.append(f'<li class="task-item"><input type="checkbox" {checked}> {match.group(2)}</li>')


class UnorderedListRule(BaseBlockRule):
    PATTERN = re.compile(r'^[\*\-]\s+(.*)$')

    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return bool(self.PATTERN.match(stripped))

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        if ctx.in_ol or ctx.in_quote or ctx.in_table:
            ctx.close_containers()
        if not ctx.in_ul:
            ctx.processed.append("<ul>")
            ctx.in_ul = True
        match = self.PATTERN.match(stripped)
        if match:
            ctx.processed.append(f"<li>{match.group(1)}</li>")


class OrderedListRule(BaseBlockRule):
    PATTERN = re.compile(r'^\d+\.\s+(.*)$')

    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return bool(self.PATTERN.match(stripped))

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        if ctx.in_ul or ctx.in_quote or ctx.in_table:
            ctx.close_containers()
        if not ctx.in_ol:
            ctx.processed.append("<ol>")
            ctx.in_ol = True
        match = self.PATTERN.match(stripped)
        if match:
            ctx.processed.append(f"<li>{match.group(1)}</li>")


class EmptyLineRule(BaseBlockRule):
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return not stripped

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        ctx.close_containers()
        ctx.processed.append("")


class RawHtmlRule(BaseBlockRule):
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return (stripped.startswith("<") and stripped.endswith(">")) or stripped.startswith("<!--")

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        ctx.close_containers()
        ctx.processed.append(line)


class ParagraphRule(BaseBlockRule):
    def matches(self, line: str, stripped: str, ctx: ParsingContext) -> bool:
        return True

    def process(self, line: str, stripped: str, ctx: ParsingContext) -> None:
        ctx.close_containers()
        ctx.processed.append(f"<p>{line}</p>")
