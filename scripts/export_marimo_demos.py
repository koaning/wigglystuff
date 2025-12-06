#!/usr/bin/env python3
"""Export every demos/*.py notebook to mkdocs/examples/<name>/index.html."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = ROOT / "demos"
DOCS_EXAMPLES_DIR = ROOT / "mkdocs" / "examples"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-export every demo even if the HTML output is up-to-date.",
    )
    return parser.parse_args(argv)


def needs_export(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime


def export_notebook(path: Path, *, force: bool = False) -> None:
    slug = path.stem
    target_dir = DOCS_EXAMPLES_DIR / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / "index.html"

    if not force and not needs_export(path, output_file):
        print(
            f"[docs] skipping {path.relative_to(ROOT)} (up-to-date)",
            file=sys.stderr,
        )
        return

    cmd = [
        "marimo",
        "-y",
        "export",
        "html-wasm",
        str(path),
        "--output",
        str(output_file),
        "--mode",
        "edit",
    ]
    print(f"[docs] exporting {path.relative_to(ROOT)} -> {output_file.relative_to(ROOT)}")
    subprocess.run(cmd, check=True)


def export_all(*, force: bool = False) -> int:
    DOCS_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    demos = sorted(DEMOS_DIR.glob("*.py"))
    if not demos:
        print("[docs] no demos/*.py files found", file=sys.stderr)
        return 1

    for demo in demos:
        export_notebook(demo, force=force)

    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(export_all(force=args.force))
