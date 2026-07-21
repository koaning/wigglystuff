"""ScatterLog -- accumulate (x, y[, color]) points into a live scatter."""

from typing import Any, Optional

from .altair_widget import AltairWidget

# Name for the accumulating dataset; altair-widget.js patches data in place by
# targeting this exact name via the Vega changeset API.
_DATASET = "scatterlog"

# Distinguishes "no y given" from a legitimate ``y=None``.
_UNSET = object()


def _jsonable(value: Any) -> Any:
    """Coerce a scalar to something JSON-serializable.

    Numpy scalars (and anything else with a zero-arg ``.item()``) become plain
    Python numbers; everything else passes through untouched. Duck-typed on
    purpose so numpy stays an optional dependency -- mirrors
    ``ObservablePlot._to_jsonable``.
    """
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except (TypeError, ValueError):
            return value
    return value


class ScatterLog(AltairWidget):
    """Accumulate ``(x, y[, color])`` points and draw them as a live scatter.

    Unlike a plain marimo state variable -- which reactivity keeps resetting --
    a ``ScatterLog`` instance is stable across cell re-runs, so it can *grow* a
    history. Create it once in its own (dependency-free) cell, then call
    ``.append(...)`` from a separate reactive cell; each re-run of that cell adds
    a point. Because ``x`` and ``y`` are passed explicitly they can come from
    different upstream widgets.

    It subclasses :class:`AltairWidget`, so appends update the chart in place via
    the Vega changeset API (no flicker, zoom/pan preserved). Read the accumulated
    points back with ``.data``.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import ScatterLog

        log = ScatterLog(x_label="energy", y_label="p(win)")
        mo.ui.anywidget(log)  # display once

        # ...in a reactive cell that depends on `slider`:
        log.append(x=slider.value, y=prob, color="run-1")
        ```
    """

    def __init__(
        self,
        *,
        x_label: str = "x",
        y_label: str = "y",
        color_label: str = "color",
        max_points: int = 500,
        width: int = 600,
        height: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a ScatterLog.

        Args:
            x_label: Axis title for the x values.
            y_label: Axis title for the y values.
            color_label: Legend title used once colored points appear.
            max_points: Keep at most this many most-recent points (bounds the
                synced history so marimo exports stay small).
            width: Chart width in pixels.
            height: Chart height in pixels.
            **kwargs: Forwarded to :class:`AltairWidget`.
        """
        if max_points < 1:
            raise ValueError(f"max_points must be >= 1, got {max_points}")
        self._points: list[dict] = []  # source of truth
        self._has_color = False  # sticky: once a color is seen, keep the legend
        self._x_label = x_label
        self._y_label = y_label
        self._color_label = color_label
        self.max_points = int(max_points)
        super().__init__(chart=None, width=width, height=height, **kwargs)

    def append(
        self, x: Any, y: Any = _UNSET, color: Optional[Any] = None, **series: Any
    ) -> None:
        """Log one or more points at ``x`` and redraw.

        A single point (``color`` optionally labels its series)::

            log.append(x=1.0, y=2.0)
            log.append(x=1.0, y=2.0, color="run-1")

        Several named series at the same ``x`` -- each keyword becomes a series
        whose name is its legend label::

            log.append(x=step, loss=0.3, acc=0.9)
        """
        if y is not _UNSET:
            self._add_point(x, y, color)
        for name, value in series.items():
            self._add_point(x, value, name)
        if len(self._points) > self.max_points:
            self._points = self._points[-self.max_points :]
        self.spec = self._build_spec()

    def _add_point(self, x: Any, y: Any, color: Optional[Any]) -> None:
        self._points.append(
            {
                "x": _jsonable(x),
                "y": _jsonable(y),
                "color": None if color is None else str(color),
            }
        )
        if color is not None:
            self._has_color = True

    def clear(self) -> None:
        """Drop all accumulated points and blank the chart."""
        self._points = []
        self.spec = {}

    @property
    def data(self) -> list[dict]:
        """A copy of the accumulated points, oldest first."""
        return list(self._points)

    def _build_spec(self) -> dict:
        encoding = {
            "x": {"field": "x", "type": "quantitative", "title": self._x_label},
            "y": {"field": "y", "type": "quantitative", "title": self._y_label},
        }
        if self._has_color:
            encoding["color"] = {
                "field": "color",
                "type": "nominal",
                "title": self._color_label,
                # Sit the legend under the x-axis so it can't get clipped off
                # the right edge of the container.
                "legend": {"orient": "bottom"},
            }
        # Emit the data as a *named* dataset (the shape Altair produces), not as
        # inline ``data.values``. altair-widget.js does its flicker-free update by
        # calling ``view.change(<dataset-name>, ...)``; inline data compiles under
        # an auto-generated name it can't target, so appends past the first would
        # silently no-op. A fresh ``list(...)`` each time also matters: aliasing
        # the live self._points list makes old/new specs compare equal, and
        # traitlets would then skip the change notification entirely.
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "datasets": {_DATASET: list(self._points)},
            "data": {"name": _DATASET},
            "mark": {"type": "point", "filled": True},
            "encoding": encoding,
        }
