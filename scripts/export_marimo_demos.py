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
LAST_BUILD_COMMIT = DOCS_EXAMPLES_DIR / ".last-build-commit"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-export every demo even if the HTML output is up-to-date.",
    )
    return parser.parse_args(argv)


def get_head_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def get_changed_demos(since_commit: str) -> set[str]:
    """Return basenames of demos/*.py files changed since the given commit."""
    result = subprocess.run(
        ["git", "diff", "--name-only", since_commit, "HEAD", "--", "demos/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {Path(line).name for line in result.stdout.splitlines() if line.strip()}


def export_notebook(path: Path) -> None:
    slug = path.stem
    target_dir = DOCS_EXAMPLES_DIR / slug
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / "index.html"

    cmd = [
        "marimo",
        "-y",
        "-q",
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

    if force or not LAST_BUILD_COMMIT.exists():
        if not force:
            print("[docs] no previous build marker found, exporting all demos")
        to_export = {d.name for d in demos}
    else:
        since = LAST_BUILD_COMMIT.read_text().strip()
        to_export = get_changed_demos(since)

    for demo in demos:
        if demo.name in to_export:
            export_notebook(demo)
        else:
            print(f"[docs] skipping {demo.relative_to(ROOT)} (unchanged)", file=sys.stderr)

    LAST_BUILD_COMMIT.write_text(get_head_commit() + "\n")
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(export_all(force=args.force))
