#!/usr/bin/env python3
"""Export every demos/*.py notebook to mkdocs/examples/<name>/index.html."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMOS_DIR = ROOT / "demos"
DOCS_EXAMPLES_DIR = ROOT / "mkdocs" / "examples"
DEMO_HASHES_FILE = DOCS_EXAMPLES_DIR / ".demo-hashes.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-export every demo even if the HTML output is up-to-date.",
    )
    return parser.parse_args(argv)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_hashes(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_hashes(path: Path, hashes: dict[str, str]) -> None:
    path.write_text(json.dumps(hashes, sort_keys=True, indent=2) + "\n")


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

    current_hashes = {d.name: hash_file(d) for d in demos}
    stored_hashes = load_hashes(DEMO_HASHES_FILE)

    if force or not DEMO_HASHES_FILE.exists():
        if not force:
            print("[docs] no previous hash file found, exporting all demos")
        to_export = {d.name for d in demos}
    else:
        to_export = {
            name for name, digest in current_hashes.items()
            if stored_hashes.get(name) != digest
        }

    for demo in demos:
        if demo.name in to_export:
            export_notebook(demo)
        else:
            print(f"[docs] skipping {demo.relative_to(ROOT)} (unchanged)", file=sys.stderr)

    save_hashes(DEMO_HASHES_FILE, current_hashes)
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(export_all(force=args.force))
