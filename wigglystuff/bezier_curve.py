from __future__ import annotations

from math import nan
from pathlib import Path
from typing import Any, Iterable

import anywidget
import traitlets


DEFAULT_POINTS = [
    {"x": 0.10, "y": 0.20},
    {"x": 0.25, "y": 0.90},
    {"x": 0.75, "y": 0.90},
    {"x": 0.90, "y": 0.20},
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


def _coerce_points(points: Iterable[dict[str, Any]] | None) -> list[dict[str, float]]:
    if points is None:
        return [point.copy() for point in DEFAULT_POINTS]
    return [_coerce_point(point) for point in points]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _effective_points(
    points: list[dict[str, float]], closed: bool
) -> list[dict[str, float]]:
    if closed and points:
        return [*points, points[0].copy()]
    return points


def _sample_points(
    points: list[dict[str, float]], closed: bool, n: int
) -> list[dict[str, float]]:
    effective = _effective_points(points, closed)
    if not effective or n < 2:
        return []
    samples = []
    for index in range(n):
        t = index / (n - 1)
        x, y = _de_casteljau(effective, t)
        samples.append({"x": x, "y": y})
    return samples


def _de_casteljau(
    points: list[dict[str, float]], t: float
) -> tuple[float, float]:
    if not points:
        return nan, nan

    level = [{"x": point["x"], "y": point["y"]} for point in points]
    amount = _clamp01(t)
    while len(level) > 1:
        level = [
            {
                "x": a["x"] + (b["x"] - a["x"]) * amount,
                "y": a["y"] + (b["y"] - a["y"]) * amount,
            }
            for a, b in zip(level, level[1:])
        ]
    return level[0]["x"], level[0]["y"]


class BezierCurve(anywidget.AnyWidget):
    """Interactive arbitrary-degree Bezier curve editor.

    Double-click to add control points, drag points to reshape the curve, and
    use the play controls to advance ``t`` from 0 to 1. Coordinates synced to
    Python use the configurable data bounds rather than SVG pixels.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import BezierCurve

        curve = mo.ui.anywidget(BezierCurve(closed=True, loop=True))
        curve
        ```
    """

    _esm = Path(__file__).parent / "static" / "bezier-curve.js"
    _css = Path(__file__).parent / "static" / "bezier-curve.css"

    points = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    samples = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    t = traitlets.Float(0.0).tag(sync=True)
    closed = traitlets.Bool(False).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    loop = traitlets.Bool(False).tag(sync=True)
    interval_ms = traitlets.Int(30).tag(sync=True)
    duration_ms = traitlets.Int(12000).tag(sync=True)
    sync_throttle_ms = traitlets.Int(250).tag(sync=True)
    show_axes = traitlets.Bool(False).tag(sync=True)
    n_samples = traitlets.Int(100).tag(sync=True)
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
        closed: bool = False,
        playing: bool = False,
        loop: bool = False,
        t: float = 0.0,
        x_bounds: tuple[float, float] = (0.0, 1.0),
        y_bounds: tuple[float, float] = (0.0, 1.0),
        width: int = 600,
        height: int = 360,
        interval_ms: int = 30,
        duration_ms: int = 12000,
        sync_throttle_ms: int = 250,
        show_axes: bool = False,
        n_samples: int = 100,
        **kwargs: Any,
    ) -> None:
        """Create a BezierCurve widget.

        Args:
            points: Initial control points as ``{"x": float, "y": float}``.
            closed: Whether to append the first point virtually for rendering.
            playing: Whether playback starts immediately.
            loop: Whether playback wraps from ``t=1`` back to ``t=0``.
            t: Initial curve parameter in ``[0, 1]``.
            x_bounds: Data-coordinate x bounds.
            y_bounds: Data-coordinate y bounds.
            width: SVG width in pixels.
            height: SVG height in pixels.
            interval_ms: Milliseconds between browser playback ticks.
            duration_ms: Milliseconds for one full ``t=0`` to ``t=1`` traversal.
            sync_throttle_ms: Minimum milliseconds between playback syncs.
            show_axes: Whether to render numeric tick marks and labels on the
                x and y axes.
            n_samples: Number of points emitted on the ``samples`` traitlet.
                Must be at least 2.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        coerced_points = _coerce_points(points)
        initial_t = _clamp01(t)
        initial_x, initial_y = _de_casteljau(
            _effective_points(coerced_points, closed), initial_t
        )
        if int(n_samples) < 2:
            raise traitlets.TraitError("n_samples must be at least 2.")
        initial_samples = _sample_points(coerced_points, closed, int(n_samples))
        super().__init__(
            points=coerced_points,
            samples=initial_samples,
            x=initial_x,
            y=initial_y,
            t=initial_t,
            closed=closed,
            playing=playing,
            loop=loop,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            width=width,
            height=height,
            interval_ms=interval_ms,
            duration_ms=duration_ms,
            sync_throttle_ms=sync_throttle_ms,
            show_axes=show_axes,
            n_samples=int(n_samples),
            **kwargs,
        )
        self.observe(self._refresh_current_point, names=["points", "t", "closed"])

    @traitlets.validate("points")
    def _validate_points(
        self, proposal: traitlets.Bunch
    ) -> list[dict[str, float]]:
        return _coerce_points(proposal.value)

    @traitlets.validate("t")
    def _validate_t(self, proposal: traitlets.Bunch) -> float:
        return _clamp01(proposal.value)

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

    @traitlets.validate("n_samples")
    def _validate_n_samples(self, proposal: traitlets.Bunch) -> int:
        value = int(proposal.value)
        if value < 2:
            raise traitlets.TraitError("n_samples must be at least 2.")
        return value

    def current_point(self) -> tuple[float, float]:
        """Return the current Bezier point at ``t`` as ``(x, y)``."""
        return _de_casteljau(_effective_points(self.points, self.closed), self.t)

    def sample(self, n: int = 100) -> list[dict[str, float]]:
        """Sample ``n`` points along the current Bezier curve."""
        if n <= 0:
            raise ValueError("n must be positive.")
        points = _effective_points(self.points, self.closed)
        if not points:
            return []
        if n == 1:
            x, y = _de_casteljau(points, 0.0)
            return [{"x": x, "y": y}]
        return [
            {"x": x, "y": y}
            for x, y in (
                _de_casteljau(points, index / (n - 1)) for index in range(n)
            )
        ]

    def _refresh_current_point(self, change: Any = None) -> None:
        x, y = self.current_point()
        self.set_trait("x", x)
        self.set_trait("y", y)
