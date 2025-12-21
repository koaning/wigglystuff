"""Copy markdown sources into the built site for LLM consumption."""

from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

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


def main() -> None:
    docs_dir, site_dir, excludes = _load_config()
    target_dir = site_dir / "llm"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(docs_dir.rglob("*.md")):
        relative = source.relative_to(docs_dir).as_posix()
        if _is_excluded(relative, excludes):
            continue
        destination = target_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"[docs] copied markdown to {target_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
