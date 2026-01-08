"""Copy markdown sources into the built site for LLM consumption."""

from __future__ import annotations

import fnmatch
import re
import shutil
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
MKDOCS_YML = ROOT / "mkdocs.yml"


def _parse_top_level_value(lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        value = line[len(prefix) :].strip()
        if value:
            return value.strip("'\"")
        # handle a simple YAML list
        values: list[str] = []
        for item in lines[index + 1 :]:
            if item and not item.startswith(" "):
                break
            stripped = item.strip()
            if stripped.startswith("-"):
                values.append(stripped[1:].strip().strip("'\""))
        if values:
            return ",".join(values)
    return None


def _load_config() -> tuple[Path, Path, list[str]]:
    lines = MKDOCS_YML.read_text(encoding="utf-8").splitlines()
    docs_dir = _parse_top_level_value(lines, "docs_dir") or "mkdocs"
    site_dir = _parse_top_level_value(lines, "site_dir") or "site"
    exclude_raw = _parse_top_level_value(lines, "exclude_docs") or ""
    excludes = [value.strip() for value in exclude_raw.split(",") if value.strip()]
    return ROOT / docs_dir, ROOT / site_dir, excludes


def _is_excluded(relative_posix: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative_posix, pattern) for pattern in patterns)


def _html_path_for(relative: str, site_dir: Path) -> Path:
    if relative == "index.md":
        return site_dir / "index.html"
    return site_dir / relative.removesuffix(".md") / "index.html"


def _extract_article_html(html: str) -> str | None:
    marker = '<article class="md-content__inner md-typeset">'
    start = html.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = html.find("</article>", start)
    if end == -1:
        return None
    return html[start:end]


class _HtmlToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._lines: list[str] = []
        self._line: list[str] = []
        self._list_stack: list[dict[str, int | str]] = []
        self._in_pre = False
        self._pre_buffer: list[str] = []
        self._pre_lang: str | None = None
        self._in_code_inline = False
        self._code_buffer: list[str] = []
        self._code_target: str = "line"
        self._skip_depth = 0
        self._in_table = False
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._row_has_th = False
        self._first_row_is_header = False
        self._in_highlight_table = False
        self._in_doc_section_title = False
        self._skip_next_table = False
        self._add_import_to_next_code = False
        self._widget_name: str | None = None
        self._capturing_h1 = False

    def get_markdown(self) -> str:
        self._flush_line()
        self._trim_trailing_blank_lines()
        return "\n".join(self._lines).strip() + "\n"

    def _trim_trailing_blank_lines(self) -> None:
        while self._lines and not self._lines[-1].strip():
            self._lines.pop()

    def _flush_line(self) -> None:
        if not self._line:
            return
        line = "".join(self._line).rstrip()
        self._lines.append(line)
        self._line = []

    def _ensure_blank_line(self) -> None:
        if self._line:
            self._flush_line()
        if not self._lines or self._lines[-1].strip():
            self._lines.append("")

    def _start_block(self) -> None:
        self._ensure_blank_line()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            self._skip_depth += 1
            return
        attr_map = {k: v or "" for k, v in attrs}
        if tag == "a" and "headerlink" in attr_map.get("class", ""):
            self._skip_depth = 1
            return
        # Track doc-section-title spans to detect Parameters sections
        if tag == "span" and "doc-section-title" in attr_map.get("class", ""):
            self._in_doc_section_title = True
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_line()
            self._ensure_blank_line()
            level = int(tag[1])
            self._line.append("#" * level + " ")
            if tag == "h1":
                self._capturing_h1 = True
        elif tag == "p":
            self._start_block()
        elif tag == "br":
            self._flush_line()
        elif tag == "ul":
            self._start_block()
            self._list_stack.append({"type": "ul", "count": 0})
        elif tag == "ol":
            self._start_block()
            self._list_stack.append({"type": "ol", "count": 1})
        elif tag == "li":
            self._flush_line()
            indent = "  " * max(len(self._list_stack) - 1, 0)
            if self._list_stack and self._list_stack[-1]["type"] == "ol":
                count = int(self._list_stack[-1]["count"])
                self._list_stack[-1]["count"] = count + 1
                bullet = f"{count}."
            else:
                bullet = "-"
            self._line.append(f"{indent}{bullet} ")
        elif tag == "pre":
            self._start_block()
            self._in_pre = True
            self._pre_buffer = []
            self._pre_lang = None
        elif tag == "code" and self._in_pre:
            class_name = attr_map.get("class", "")
            match = re.search(r"language-([a-zA-Z0-9_+-]+)", class_name)
            if match:
                self._pre_lang = match.group(1)
        elif tag == "code":
            self._in_code_inline = True
            self._code_buffer = []
            self._code_target = "cell" if self._in_table else "line"
        elif tag in {"strong", "b"}:
            self._line.append("**")
        elif tag in {"em", "i"}:
            self._line.append("*")
        elif tag == "table":
            if "highlighttable" in attr_map.get("class", ""):
                self._in_highlight_table = True
                return
            # Skip parameters table (table following "Parameters:" section title)
            if self._skip_next_table:
                self._skip_next_table = False
                self._skip_depth = 1
                return
            self._start_block()
            self._in_table = True
            self._table_rows = []
            self._current_row = []
            self._current_cell = []
            self._row_has_th = False
            self._first_row_is_header = False
        elif tag == "td" and self._in_highlight_table and "linenos" in attr_map.get("class", ""):
            self._skip_depth = 1
        elif tag == "tr" and self._in_table:
            self._current_row = []
            self._row_has_th = False
        elif tag in {"th", "td"} and self._in_table:
            self._current_cell = []
            if tag == "th":
                self._row_has_th = True

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush_line()
            self._ensure_blank_line()
        elif tag == "p":
            self._flush_line()
            self._ensure_blank_line()
        elif tag in {"ul", "ol"}:
            if self._list_stack:
                self._list_stack.pop()
            self._flush_line()
            self._ensure_blank_line()
        elif tag == "li":
            self._flush_line()
        elif tag == "pre":
            self._in_pre = False
            self._flush_pre()
        elif tag == "code" and self._in_code_inline:
            code_text = "".join(self._code_buffer).strip()
            if code_text:
                wrapped = f"`{code_text}`"
                if self._code_target == "cell":
                    self._current_cell.append(wrapped)
                else:
                    self._line.append(wrapped)
            self._in_code_inline = False
        elif tag in {"strong", "b"}:
            self._line.append("**")
        elif tag in {"em", "i"}:
            self._line.append("*")
        elif tag in {"th", "td"} and self._in_table:
            cell_text = "".join(self._current_cell).strip()
            self._current_row.append(cell_text)
            self._current_cell = []
        elif tag == "tr" and self._in_table:
            if self._current_row:
                if not self._table_rows:
                    self._first_row_is_header = self._row_has_th
                self._table_rows.append(self._current_row)
            self._current_row = []
        elif tag == "table":
            if self._in_highlight_table:
                self._in_highlight_table = False
                return
            self._emit_table()
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        # Capture widget name from H1 heading (e.g., "Slider2D API" -> "Slider2D")
        if self._capturing_h1:
            title = data.strip()
            if title.endswith(" API"):
                self._widget_name = title[:-4]
            self._capturing_h1 = False
        # Check if we're in a doc-section-title
        if self._in_doc_section_title:
            section_title = data.strip()
            if section_title == "Parameters:":
                self._skip_next_table = True
            elif section_title == "Examples:" and self._widget_name:
                self._add_import_to_next_code = True
            self._in_doc_section_title = False
            return
        if self._in_pre:
            self._pre_buffer.append(data)
            return
        if self._in_code_inline:
            self._code_buffer.append(data)
            return
        text = data
        text = re.sub(r"\s+", " ", text)
        if not text:
            return
        if self._in_table and self._current_cell is not None:
            self._current_cell.append(text)
            return
        if self._line and self._line[-1].endswith(" "):
            text = text.lstrip()
        self._line.append(text)

    def _flush_pre(self) -> None:
        pre_text = "".join(self._pre_buffer)
        pre_text = pre_text.rstrip("\n")
        # Prepend import statement to examples code block
        if self._add_import_to_next_code and self._widget_name:
            import_line = f"from wigglystuff import {self._widget_name}\n\n"
            pre_text = import_line + pre_text
            self._add_import_to_next_code = False
        fence = f"```{self._pre_lang or ''}".rstrip()
        self._lines.append(fence)
        if pre_text:
            self._lines.extend(pre_text.splitlines())
        self._lines.append("```")
        self._lines.append("")
        self._pre_buffer = []
        self._pre_lang = None

    def _emit_table(self) -> None:
        if not self._table_rows:
            return
        column_count = max(len(row) for row in self._table_rows)
        rows = [row + [""] * (column_count - len(row)) for row in self._table_rows]
        if self._first_row_is_header:
            header = rows[0]
            body = rows[1:]
        else:
            header = [""] * column_count
            body = rows
        header_line = "| " + " | ".join(self._escape_cell(cell) for cell in header) + " |"
        separator = "| " + " | ".join("---" for _ in header) + " |"
        self._lines.append(header_line)
        self._lines.append(separator)
        for row in body:
            row_line = "| " + " | ".join(self._escape_cell(cell) for cell in row) + " |"
            self._lines.append(row_line)
        self._lines.append("")

    @staticmethod
    def _escape_cell(value: str) -> str:
        return value.replace("|", r"\|").strip()


def _html_to_markdown(html: str) -> str:
    parser = _HtmlToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


def main() -> None:
    docs_dir, site_dir, excludes = _load_config()
    legacy_dir = site_dir / "llm"
    if legacy_dir.exists():
        shutil.rmtree(legacy_dir)

    # Copy llms.txt if it exists
    llms_txt_source = docs_dir / "llms.txt"
    if llms_txt_source.exists():
        site_dir.mkdir(parents=True, exist_ok=True)
        llms_txt_dest = site_dir / "llms.txt"
        shutil.copy2(llms_txt_source, llms_txt_dest)
        print(f"[docs] copied llms.txt to {site_dir.relative_to(ROOT)}")

    for source in sorted(docs_dir.rglob("*.md")):
        relative = source.relative_to(docs_dir).as_posix()
        if _is_excluded(relative, excludes):
            continue
        destination = site_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        html_path = _html_path_for(relative, site_dir)
        if html_path.exists():
            html = html_path.read_text(encoding="utf-8")
            article_html = _extract_article_html(html)
            if article_html:
                markdown = _html_to_markdown(article_html)
                destination.write_text(markdown, encoding="utf-8")
                continue
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"[docs] copied markdown to {site_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
