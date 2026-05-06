"""Convert all PNGs under docs/assets/ to WebP, deleting the originals.

Run with: uv run python scripts/png_to_webp.py
"""

from pathlib import Path

from PIL import Image

ASSETS_DIR = Path(__file__).resolve().parent.parent / "docs" / "assets"
QUALITY = 85


def main() -> None:
    pngs = sorted(ASSETS_DIR.rglob("*.png"))
    if not pngs:
        print(f"No PNGs found under {ASSETS_DIR}")
        return

    total_before = 0
    total_after = 0
    for png in pngs:
        webp = png.with_suffix(".webp")
        before = png.stat().st_size
        with Image.open(png) as img:
            img.save(webp, format="WEBP", quality=QUALITY, method=6)
        after = webp.stat().st_size
        png.unlink()
        total_before += before
        total_after += after
        print(
            f"{png.relative_to(ASSETS_DIR)}: "
            f"{before / 1024:.1f}K -> {after / 1024:.1f}K "
            f"({100 * (1 - after / before):.0f}% smaller)"
        )

    print(
        f"\nTotal: {total_before / 1024 / 1024:.2f} MB -> "
        f"{total_after / 1024 / 1024:.2f} MB "
        f"({100 * (1 - total_after / total_before):.0f}% smaller, "
        f"{len(pngs)} files)"
    )


if __name__ == "__main__":
    main()
