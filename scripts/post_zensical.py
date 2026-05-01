"""Post-process a `zensical build` so the wigglystuff site matches what the
mkdocs flow used to produce:

1. Copy each `.md` source into `site/`, rendering reference pages from the
   built HTML so the served `.md` contains the expanded docstring (matching
   what `scripts/copy_docs_md.py` produces for the mkdocs flow).
2. Restore gallery `MD` link hrefs that zensical's link extension rewrites
   to their HTML directory equivalent.

The zensical equivalent of `scripts/copy_docs_md.py` — kept separate because
copy_docs_md.py keys off mkdocs.yml and is shaped around mkdocs-material's
HTML output.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "mkdocs"
SITE_DIR = ROOT / "site"

sys.path.insert(0, str(Path(__file__).parent))
from copy_docs_md import _HtmlToMarkdown, _extract_article_html  # noqa: E402


def _html_path_for(relative: str) -> Path:
    if relative == "index.md":
        return SITE_DIR / "index.html"
    return SITE_DIR / relative.removesuffix(".md") / "index.html"


def _copy_markdown_sources() -> None:
    for source in sorted(DOCS_DIR.rglob("*.md")):
        relative = source.relative_to(DOCS_DIR).as_posix()
        destination = SITE_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        html_path = _html_path_for(relative)
        if html_path.exists():
            html = html_path.read_text(encoding="utf-8")
            article_html = _extract_article_html(html)
            if article_html:
                parser = _HtmlToMarkdown()
                parser.feed(article_html)
                destination.write_text(parser.get_markdown(), encoding="utf-8")
                continue
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


_MD_LINK_PATTERN = re.compile(
    r'<a href="((?:\.\.?/)*)reference/([^/"]+)/">MD</a>'
)


def _patch_md_links() -> None:
    for html_file in SITE_DIR.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        patched = _MD_LINK_PATTERN.sub(
            r'<a href="\1reference/\2.md">MD</a>',
            text,
        )
        if patched != text:
            html_file.write_text(patched, encoding="utf-8")


def main() -> None:
    _copy_markdown_sources()
    _patch_md_links()
    print(f"[post-zensical] copied .md sources and patched gallery MD links in {SITE_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
