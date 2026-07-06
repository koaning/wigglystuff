from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import anywidget
import traitlets


Point = tuple[int, int]


def _ensure_positive_int(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive int.")
    return value


def _normalize_line_width(value: int | Sequence[int]) -> int | list[int]:
    if isinstance(value, int) and not isinstance(value, bool):
        return _ensure_positive_int("line_width", value)
    if not isinstance(value, (list, tuple)) or len(value) == 0:
        raise ValueError("line_width must be a positive int or a non-empty list of positive ints.")
    normalized = []
    for width in value:
        normalized.append(_ensure_positive_int("line_width", width))
    return normalized


def _normalize_point(point: Sequence[int]) -> Point:
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        raise ValueError("point must be a (row, col) pair.")
    row, col = point
    if not isinstance(row, int) or isinstance(row, bool):
        raise ValueError("point row must be an int.")
    if not isinstance(col, int) or isinstance(col, bool):
        raise ValueError("point col must be an int.")
    return row, col


def _canonical_segment(a: Sequence[int], b: Sequence[int]) -> tuple[Point, Point]:
    point_a = _normalize_point(a)
    point_b = _normalize_point(b)
    return tuple(sorted((point_a, point_b)))  # type: ignore[return-value]


class GridDraw(anywidget.AnyWidget):
    """Drawable square grid widget for dots and orthogonal line segments.

    `rows` and `cols` count cells. Intersections are addressed as
    `[row, col]` coordinates from `[0, 0]` through `[rows, cols]`.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import GridDraw

        grid = mo.ui.anywidget(GridDraw(rows=8, cols=8, line_width=[1, 2, 4]))
        grid
        ```
    """

    _esm = Path(__file__).parent / "static" / "griddraw.js"
    _css = Path(__file__).parent / "static" / "griddraw.css"

    dots = traitlets.List([]).tag(sync=True)
    lines = traitlets.List([]).tag(sync=True)
    rows = traitlets.Int(8).tag(sync=True)
    cols = traitlets.Int(8).tag(sync=True)
    line_width = traitlets.Any(2).tag(sync=True)
    dot_radius = traitlets.Int(6).tag(sync=True)
    theme = traitlets.Any(None).tag(sync=True)
    width = traitlets.Int(440).tag(sync=True)
    height = traitlets.Int(440).tag(sync=True)

    def __init__(
        self,
        rows: int = 8,
        cols: int = 8,
        line_width: int | Sequence[int] = 2,
        dot_radius: int = 6,
        theme: str | None = None,
        width: int = 440,
        height: int = 440,
        dots: Iterable[Sequence[int]] | None = None,
        lines: Iterable[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a GridDraw widget.

        Args:
            rows: Number of grid cells vertically.
            cols: Number of grid cells horizontally.
            line_width: Positive int for fixed width, or non-empty list of
                positive ints to show a width picker. The first list item is
                the default width.
            dot_radius: Drawn dot radius in pixels.
            theme: ``None`` follows the notebook; ``"light"`` or ``"dark"``
                force the widget theme.
            width: Widget pixel width.
            height: Widget pixel height.
            dots: Optional initial dot coordinates.
            lines: Optional initial line dictionaries.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        rows = _ensure_positive_int("rows", rows)
        cols = _ensure_positive_int("cols", cols)
        line_width = _normalize_line_width(line_width)
        dot_radius = _ensure_positive_int("dot_radius", dot_radius)
        width = _ensure_positive_int("width", width)
        height = _ensure_positive_int("height", height)
        self._validate_theme_value(theme)

        super().__init__(
            rows=rows,
            cols=cols,
            line_width=line_width,
            dot_radius=dot_radius,
            theme=theme,
            width=width,
            height=height,
            dots=[],
            lines=[],
            **kwargs,
        )
        for dot in dots or []:
            row, col = _normalize_point(dot)
            self.add_dot(row, col)
        for line in lines or []:
            self.add_line(line["from"], line["to"], width=line.get("width"))

    @staticmethod
    def _validate_theme_value(value: str | None) -> None:
        if value not in (None, "light", "dark"):
            raise ValueError('theme must be None, "light", or "dark".')

    def _default_line_width(self) -> int:
        if isinstance(self.line_width, list):
            return self.line_width[0]
        return self.line_width

    def _validate_intersection(self, point: Sequence[int]) -> Point:
        row, col = _normalize_point(point)
        if not (0 <= row <= self.rows and 0 <= col <= self.cols):
            raise ValueError(
                f"intersection ({row}, {col}) is outside the grid "
                f"0..{self.rows} by 0..{self.cols}."
            )
        return row, col

    def _validate_segment(self, a: Sequence[int], b: Sequence[int]) -> tuple[Point, Point]:
        point_a = self._validate_intersection(a)
        point_b = self._validate_intersection(b)
        row_delta = abs(point_a[0] - point_b[0])
        col_delta = abs(point_a[1] - point_b[1])
        if row_delta + col_delta != 1:
            raise ValueError("line endpoints must be orthogonally adjacent intersections.")
        return _canonical_segment(point_a, point_b)

    @traitlets.validate("line_width")
    def _validate_line_width_trait(self, proposal: traitlets.Bunch) -> int | list[int]:
        return _normalize_line_width(proposal.value)

    @traitlets.validate("rows", "cols", "dot_radius", "width", "height")
    def _validate_positive_int_trait(self, proposal: traitlets.Bunch) -> int:
        return _ensure_positive_int(proposal.trait.name, proposal.value)

    @traitlets.validate("theme")
    def _validate_theme_trait(self, proposal: traitlets.Bunch) -> str | None:
        self._validate_theme_value(proposal.value)
        return proposal.value

    def add_dot(self, row: int, col: int) -> None:
        """Add a dot at an intersection.

        Adding an existing dot is a no-op.
        """
        point = list(self._validate_intersection((row, col)))
        if point not in self.dots:
            self.dots = [*self.dots, point]

    def add_line(
        self,
        a: Sequence[int],
        b: Sequence[int],
        width: int | None = None,
    ) -> None:
        """Add a unit line segment between orthogonally adjacent intersections."""
        point_a, point_b = self._validate_segment(a, b)
        if width is None:
            width = self._default_line_width()
        width = _ensure_positive_int("width", width)
        start = list(point_a)
        end = list(point_b)
        if any(line.get("from") == start and line.get("to") == end for line in self.lines):
            return
        self.lines = [*self.lines, {"from": start, "to": end, "width": width}]

    def clear(self) -> None:
        """Remove all dots and lines."""
        self.dots = []
        self.lines = []
