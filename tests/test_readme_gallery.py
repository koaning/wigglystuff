"""Linter for the README widget-gallery table.

The gallery in ``README.md`` is a hand-maintained HTML ``<table>``: one ``<tr>``
per row, three ``<td>`` cards per row. It quietly breaks whenever a widget is
added by hand (a row ends up with 4 cells, a screenshot goes missing, a molab
link loses its ``utm_source``). These tests assert the structural invariants so
the grid stops drifting.

Parsing is deliberately regex-based (stdlib only) to keep the check obvious.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
GALLERY_DIR = REPO_ROOT / "docs" / "assets" / "gallery"

TABLE_RE = re.compile(r"<table>(.*?)</table>", re.S)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
HREF_RE = re.compile(r'<a\s+href="([^"]+)"')
IMG_SRC_RE = re.compile(r'<img\s+src="([^"]+)"')
NAME_RE = re.compile(r"<b>(.*?)</b>")
GALLERY_IMG_RE = re.compile(r"^\./docs/assets/gallery/(.+)\.webp$")


def gallery_tables():
    """Every ``<table>`` in the README as ``[table][row][cell_html]``."""
    text = README.read_text()
    tables = []
    for tbl in TABLE_RE.findall(text):
        tables.append([CELL_RE.findall(row) for row in ROW_RE.findall(tbl)])
    return tables


def cell_name(cell):
    m = NAME_RE.search(cell)
    return m.group(1) if m else "<unnamed>"


def all_cells():
    """Yield ``(label, cell_html)`` for every gallery card across all tables."""
    for ti, table in enumerate(gallery_tables()):
        for ri, row in enumerate(table):
            for ci, cell in enumerate(row):
                yield f"table {ti} row {ri} col {ci} ({cell_name(cell)})", cell


def ref_slug(href):
    """The ``<slug>`` in ``.../reference/<slug>/`` or ``.../reference/<slug>.md``."""
    m = re.search(r"/reference/(.+?)(?:/|\.md)$", href)
    return m.group(1) if m else None


def test_gallery_rows_have_exactly_three_cells():
    """3 cells per row keeps the grid even; only a final row may be shorter."""
    problems = []
    for ti, table in enumerate(gallery_tables()):
        for ri, row in enumerate(table):
            n = len(row)
            is_last = ri == len(table) - 1
            if not (n == 3 or (is_last and 1 <= n < 3)):
                names = ", ".join(cell_name(c) for c in row)
                problems.append(f"table {ti} row {ri}: {n} cells ({names})")
    assert not problems, (
        "Gallery rows must have exactly 3 cells (the final row may have 1-2):\n"
        + "\n".join(problems)
    )


def test_gallery_cells_are_well_formed():
    """Every card has a name, one gallery thumbnail, and molab/API/MD links."""
    problems = []
    for label, cell in all_cells():
        if not NAME_RE.search(cell):
            problems.append(f"{label}: missing <b>name</b>")
        imgs = IMG_SRC_RE.findall(cell)
        if len(imgs) != 1 or not GALLERY_IMG_RE.match(imgs[0]):
            problems.append(f"{label}: expected one ./docs/assets/gallery/*.webp img, got {imgs}")
        if len(HREF_RE.findall(cell)) != 4:
            problems.append(f"{label}: expected 4 links (thumb, molab, API, MD)")
    assert not problems, "Malformed gallery cells:\n" + "\n".join(problems)


def test_gallery_screenshots_exist():
    """Each referenced screenshot exists under docs/assets/gallery/."""
    problems = []
    for label, cell in all_cells():
        for src in IMG_SRC_RE.findall(cell):
            m = GALLERY_IMG_RE.match(src)
            if m and not (GALLERY_DIR / f"{m.group(1)}.webp").exists():
                problems.append(f"{label}: missing screenshot {src}")
    assert not problems, "Referenced screenshots do not exist:\n" + "\n".join(problems)


def test_gallery_molab_links_carry_utm_source():
    """Every molab link must be attributable (CLAUDE.md hard requirement)."""
    problems = []
    for label, cell in all_cells():
        for href in HREF_RE.findall(cell):
            if "molab.marimo.io" in href and "utm_source=wigglystuff" not in href:
                problems.append(f"{label}: {href}")
    assert not problems, "molab links missing ?utm_source=wigglystuff:\n" + "\n".join(problems)


def test_gallery_intra_cell_links_are_consistent():
    """The two molab hrefs match, and the API/MD links share one reference slug."""
    problems = []
    for label, cell in all_cells():
        hrefs = HREF_RE.findall(cell)
        if len(hrefs) != 4:
            continue  # shape is reported by test_gallery_cells_are_well_formed
        thumb, molab, api, md = hrefs
        if thumb != molab:
            problems.append(f"{label}: thumbnail and molab links differ")
        if ref_slug(api) != ref_slug(md):
            problems.append(f"{label}: API slug {ref_slug(api)!r} != MD slug {ref_slug(md)!r}")
    assert not problems, "Inconsistent gallery cell links:\n" + "\n".join(problems)
