"""Step-through LaTeX derivation animation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "formula-animation.js"
_CSS_PATH = Path(__file__).parent / "static" / "formula-animation.css"


def _normalize_steps(steps: Any) -> list[dict[str, str]]:
    """Validate and normalize the ``steps`` input to ``[{"tex", "note"}]``.

    Each entry must be a mapping with a non-empty string ``tex``; an optional
    ``note`` becomes ``""`` when missing. The caller's input is never mutated.
    """
    if isinstance(steps, (str, bytes, Mapping)) or not isinstance(steps, Sequence):
        raise ValueError("steps must be a list of dicts, each with a 'tex' key.")
    if len(steps) == 0:
        raise ValueError("steps must contain at least one step.")

    normalized: list[dict[str, str]] = []
    for index, raw in enumerate(steps):
        if not isinstance(raw, Mapping):
            raise ValueError(f"step {index} must be a mapping with a 'tex' key.")
        tex = raw.get("tex")
        if not isinstance(tex, str) or not tex.strip():
            raise ValueError(f"step {index} must have a non-empty string 'tex'.")
        note = raw.get("note", "")
        if note is None:
            note = ""
        if not isinstance(note, str):
            raise ValueError(f"step {index} 'note' must be a string.")
        normalized.append({"tex": tex, "note": note})
    return normalized


class FormulaAnimation(anywidget.AnyWidget):
    r"""Animate a LaTeX derivation one step at a time.

    Give it a list of ``{"tex": ..., "note": ...}`` steps and it renders a
    stack of KaTeX equations where the current line sits centered, the previous
    line floats above it dimmed, and a short caption shows under the active
    line. Playback is manual: move through the derivation with the built-in
    prev/next buttons, with the arrow keys (after clicking the widget to enable
    them), or by driving the ``step`` trait from Python (e.g. a marimo slider).

    With ``spotlight=True`` a final step frames the last formula alone in a
    boxed, slightly zoomed state so the finished result stands out.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import FormulaAnimation

        anim = mo.ui.anywidget(
            FormulaAnimation(
                title="The abc-formula",
                steps=[
                    {"tex": r"ax^2 + bx + c = 0", "note": "A quadratic equation, with a ≠ 0."},
                    {"tex": r"x^2 + \tfrac{b}{a}x + \tfrac{c}{a} = 0", "note": "Make the leading coefficient 1."},
                    {"tex": r"x = \dfrac{-b \pm \sqrt{b^2 - 4ac}}{2a}", "note": "The abc-formula."},
                ],
            )
        )
        anim
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    steps = traitlets.List(traitlets.Dict()).tag(sync=True)
    title = traitlets.Unicode(allow_none=True, default_value=None).tag(sync=True)
    spotlight = traitlets.Bool(True).tag(sync=True)
    step = traitlets.Int(0).tag(sync=True)
    height = traitlets.Int(360).tag(sync=True)
    theme = traitlets.Enum(["auto", "light", "dark"], default_value="auto").tag(
        sync=True
    )
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        steps: Sequence[Mapping[str, Any]],
        *,
        title: str | None = None,
        spotlight: bool = True,
        height: int = 360,
        theme: str = "auto",
        **kwargs: Any,
    ) -> None:
        """Create a FormulaAnimation widget.

        Args:
            steps: List of ``{"tex": str, "note": str}`` dicts. ``tex`` is
                required (raw LaTeX passed to KaTeX); ``note`` is an optional
                caption shown under the active line.
            title: Optional heading rendered above the animation.
            spotlight: Append a final step framing the last formula alone.
            height: Height of the animation stage in pixels.
            theme: Color theme: ``"auto"``, ``"light"``, or ``"dark"``.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if title is not None and not isinstance(title, str):
            raise ValueError("title must be a string or None.")
        if theme not in {"auto", "light", "dark"}:
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")
        if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
            raise ValueError("height must be a positive integer.")

        normalized = _normalize_steps(steps)
        super().__init__(
            steps=normalized,
            title=title,
            spotlight=spotlight,
            height=height,
            theme=theme,
            **kwargs,
        )
