#!/usr/bin/env python3
"""Export every demos/*.py notebook to mkdocs/examples/<name>/index.html."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = ROOT / "demos"
DOCS_EXAMPLES_DIR = ROOT / "mkdocs" / "examples"


def export_notebook(path: Path) -> None:
    slug = path.stem
    target_dir = DOCS_EXAMPLES_DIR / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / "index.html"

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


def main() -> int:
    DOCS_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    demos = sorted(DEMOS_DIR.glob("*.py"))
    if not demos:
        print("[docs] no demos/*.py files found", file=sys.stderr)
        return 1

    for demo in demos:
        export_notebook(demo)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
