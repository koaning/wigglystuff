from __future__ import annotations

from math import nan
from pathlib import Path
from typing import Any, Iterable

import anywidget
import traitlets


CURVES = {
    "linear",
    "step",
    "step_before",
    "step_after",
    "basis",
    "natural",
    "cardinal",
    "catmull_rom",
    "monotone_x",
    "bump_x",
}

DEFAULT_POINTS = [
    {"x": 0.00, "y": 0.15},
    {"x": 0.18, "y": 0.32},
    {"x": 0.38, "y": 0.72},
    {"x": 0.62, "y": 0.48},
    {"x": 0.82, "y": 0.88},
    {"x": 1.00, "y": 0.58},
]


def _coerce_point(point: dict[str, Any]) -> dict[str, float]:
    if not isinstance(point, dict):
        raise traitlets.TraitError("Each point must be a dict with x and y values.")
    if "x" not in point or "y" not in point:
        raise traitlets.TraitError("Each point must have x and y values.")
    try:
        return {"x": float(point["x"]), "y": float(point["y"])}
    except (TypeError, ValueError) as exc:
        raise traitlets.TraitError("Point x and y values must be numeric.") from exc


def _coerce_points(
    points: Iterable[dict[str, Any]] | None,
    *,
    sort_by_x: bool = True,
) -> list[dict[str, float]]:
    if points is None:
        points = DEFAULT_POINTS
    coerced = [_coerce_point(point) for point in points]
    if len(coerced) < 2:
        raise traitlets.TraitError("CurveEditor requires at least two points.")
    if sort_by_x:
        return sorted(coerced, key=lambda point: point["x"])
    return coerced


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _effective_points(
    points: list[dict[str, float]], closed: bool
) -> list[dict[str, float]]:
    if closed and points:
        return [*points, points[0].copy()]
    return points


def _point_at_t(
    points: list[dict[str, float]], t: float
) -> tuple[float, float]:
    """Approximate the browser path position with linear segment distance."""
    if not points:
        return nan, nan
    if len(points) == 1:
        return points[0]["x"], points[0]["y"]

    segments = []
    total = 0.0
    for start, end in zip(points, points[1:]):
        length = ((end["x"] - start["x"]) ** 2 + (end["y"] - start["y"]) ** 2) ** 0.5
        segments.append((start, end, length))
        total += length
    if total == 0:
        return points[0]["x"], points[0]["y"]

    target = _clamp01(t) * total
    walked = 0.0
    for start, end, length in segments:
        if walked + length >= target:
            amount = 0.0 if length == 0 else (target - walked) / length
            return (
                start["x"] + (end["x"] - start["x"]) * amount,
                start["y"] + (end["y"] - start["y"]) * amount,
            )
        walked += length
    return points[-1]["x"], points[-1]["y"]


class CurveEditor(anywidget.AnyWidget):
    """Chart-space curve editor powered by D3 line interpolators.

    Drag knots on an x/y chart and switch among D3's chart-oriented curve
    factories. Open curves store points in x order so step, monotone, and bump
    curves behave like normal chart lines instead of freeform paths. Closed
    curves preserve point order so they can be edited as drawn loops.

    Examples:
        ```python
        from wigglystuff import CurveEditor

        editor = CurveEditor(curve="catmull_rom", alpha=0.5)
        editor
        ```
    """

    _esm = Path(__file__).parent / "static" / "curve-editor.js"
    _css = Path(__file__).parent / "static" / "curve-editor.css"

    points = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    t = traitlets.Float(0.0).tag(sync=True)
    curve = traitlets.Unicode("natural").tag(sync=True)
    tension = traitlets.Float(0.0).tag(sync=True)
    alpha = traitlets.Float(0.5).tag(sync=True)
    closed = traitlets.Bool(False).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    loop = traitlets.Bool(False).tag(sync=True)
    interval_ms = traitlets.Int(30).tag(sync=True)
    duration_ms = traitlets.Int(12000).tag(sync=True)
    sync_throttle_ms = traitlets.Int(250).tag(sync=True)
    selected_index = traitlets.Int(-1).tag(sync=True)
    x_bounds = (
        traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
        ).tag(sync=True)
    )
    y_bounds = (
        traitlets.Tuple(
            traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
        ).tag(sync=True)
    )
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(360).tag(sync=True)

    def __init__(
        self,
        points: Iterable[dict[str, Any]] | None = None,
        *,
        curve: str = "natural",
        x_bounds: tuple[float, float] = (0.0, 1.0),
        y_bounds: tuple[float, float] = (0.0, 1.0),
        width: int = 600,
        height: int = 360,
        tension: float = 0.0,
        alpha: float = 0.5,
        closed: bool = False,
        playing: bool = False,
        loop: bool = False,
        t: float = 0.0,
        interval_ms: int = 30,
        duration_ms: int = 12000,
        sync_throttle_ms: int = 250,
        selected_index: int = -1,
        **kwargs: Any,
    ) -> None:
        """Create a CurveEditor widget.

        Args:
            points: Initial knots as ``{"x": float, "y": float}`` dicts.
                Open curves store points sorted by x-coordinate. Closed curves
                preserve point order.
            curve: D3 curve name. One of ``linear``, ``step``,
                ``step_before``, ``step_after``, ``basis``, ``natural``,
                ``cardinal``, ``catmull_rom``, ``monotone_x``, or ``bump_x``.
            x_bounds: Data-coordinate x bounds.
            y_bounds: Data-coordinate y bounds.
            width: SVG width in pixels.
            height: SVG height in pixels.
            tension: Cardinal spline tension, clamped to ``[0, 1]``.
            alpha: Catmull-Rom alpha, clamped to ``[0, 1]``.
            closed: Whether to append the first point virtually when rendering.
            playing: Whether playback starts immediately.
            loop: Whether playback wraps from ``t=1`` back to ``t=0``.
            t: Initial path progress in ``[0, 1]``.
            interval_ms: Milliseconds between browser playback ticks.
            duration_ms: Milliseconds for one full ``t=0`` to ``t=1`` traversal.
            sync_throttle_ms: Minimum milliseconds between playback updates synced to Python.
            selected_index: Selected point index, or ``-1``.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        coerced_points = _coerce_points(points, sort_by_x=not closed)
        initial_t = _clamp01(t)
        initial_x, initial_y = _point_at_t(
            _effective_points(coerced_points, closed), initial_t
        )
        super().__init__(
            closed=closed,
            points=coerced_points,
            x=initial_x,
            y=initial_y,
            t=initial_t,
            curve=curve,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            width=width,
            height=height,
            tension=tension,
            alpha=alpha,
            playing=playing,
            loop=loop,
            interval_ms=interval_ms,
            duration_ms=duration_ms,
            sync_throttle_ms=sync_throttle_ms,
            selected_index=selected_index,
            **kwargs,
        )
        self.observe(self._refresh_current_point, names=["points", "t", "closed"])
        self.observe(self._sort_points_when_opened, names=["closed"])

    @traitlets.validate("points")
    def _validate_points(
        self, proposal: traitlets.Bunch
    ) -> list[dict[str, float]]:
        return _coerce_points(proposal.value, sort_by_x=not self.closed)

    @traitlets.validate("curve")
    def _validate_curve(self, proposal: traitlets.Bunch) -> str:
        value = str(proposal.value)
        if value not in CURVES:
            allowed = ", ".join(sorted(CURVES))
            raise traitlets.TraitError(f"curve must be one of: {allowed}.")
        return value

    @traitlets.validate("x_bounds", "y_bounds")
    def _validate_bounds(self, proposal: traitlets.Bunch) -> tuple[float, float]:
        low, high = proposal.value
        low = float(low)
        high = float(high)
        if low >= high:
            raise traitlets.TraitError("Bounds must have min < max.")
        return low, high

    @traitlets.validate("width", "height")
    def _validate_size(self, proposal: traitlets.Bunch) -> int:
        value = proposal.value
        if value <= 0:
            raise traitlets.TraitError(f"{proposal.trait.name} must be positive.")
        return value

    @traitlets.validate("tension", "alpha")
    def _validate_curve_parameter(self, proposal: traitlets.Bunch) -> float:
        return _clamp01(proposal.value)

    @traitlets.validate("t")
    def _validate_t(self, proposal: traitlets.Bunch) -> float:
        return _clamp01(proposal.value)

    @traitlets.validate("interval_ms")
    def _validate_interval_ms(self, proposal: traitlets.Bunch) -> int:
        value = proposal.value
        if value <= 0:
            raise traitlets.TraitError("interval_ms must be positive.")
        return value

    @traitlets.validate("duration_ms")
    def _validate_duration_ms(self, proposal: traitlets.Bunch) -> int:
        value = proposal.value
        if value <= 0:
            raise traitlets.TraitError("duration_ms must be positive.")
        return value

    @traitlets.validate("sync_throttle_ms")
    def _validate_sync_throttle_ms(self, proposal: traitlets.Bunch) -> int:
        value = proposal.value
        if value < 0:
            raise traitlets.TraitError("sync_throttle_ms must be non-negative.")
        return value

    @traitlets.validate("selected_index")
    def _validate_selected_index(self, proposal: traitlets.Bunch) -> int:
        value = int(proposal.value)
        if value < -1:
            raise traitlets.TraitError("selected_index must be -1 or non-negative.")
        if hasattr(self, "points") and self.points and value >= len(self.points):
            raise traitlets.TraitError("selected_index is outside the points list.")
        return value

    def current_point(self) -> tuple[float, float]:
        """Return the current path progress point as ``(x, y)``.

        In Python this is a linear distance approximation through the knots.
        The browser syncs ``x`` and ``y`` from the actual rendered D3 SVG path
        whenever the widget is displayed.
        """
        return _point_at_t(_effective_points(self.points, self.closed), self.t)

    def _refresh_current_point(self, change: Any = None) -> None:
        x, y = self.current_point()
        self.set_trait("x", x)
        self.set_trait("y", y)

    def _sort_points_when_opened(self, change: traitlets.Bunch) -> None:
        if change.new:
            return
        selected_point = None
        if 0 <= self.selected_index < len(self.points):
            selected_point = self.points[self.selected_index]

        sorted_points = _coerce_points(self.points, sort_by_x=True)
        if sorted_points == self.points:
            return

        self.set_trait("points", sorted_points)
        if selected_point is not None:
            try:
                self.set_trait("selected_index", sorted_points.index(selected_point))
            except ValueError:
                self.set_trait("selected_index", -1)
