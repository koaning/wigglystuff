from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class ThreeWidget(anywidget.AnyWidget):
    """Interactive 3D scatter plot powered by Three.js.

    The widget renders a collection of 3D points with per-point color and size
    attributes, suitable for quick exploratory visualizations in notebook
    environments.

    Examples:
        ```python
        data = [
            {"x": 1.0, "y": 2.0, "z": 3.0, "color": "tomato", "size": 0.2},
            {"x": -1.0, "y": 0.5, "z": -2.0, "color": "#22c55e", "size": 0.15},
        ]
        widget = ThreeWidget(data=data, show_grid=True, show_axes=True)
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "three-widget.js"
    _css = Path(__file__).parent / "static" / "three-widget.css"

    data = traitlets.List([]).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    show_grid = traitlets.Bool(False).tag(sync=True)
    show_axes = traitlets.Bool(False).tag(sync=True)
    dark_mode = traitlets.Bool(False).tag(sync=True)
    axis_labels = traitlets.List(traitlets.Unicode(), default_value=[]).tag(sync=True)
    animate_updates = traitlets.Bool(False).tag(sync=True)
    animation_duration_ms = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        *,
        data: Optional[Iterable[dict[str, Any]]] = None,
        width: int = 600,
        height: int = 400,
        show_grid: bool = False,
        show_axes: bool = False,
        dark_mode: bool = False,
        axis_labels: Optional[Iterable[str]] = None,
        animate_updates: bool = False,
        animation_duration_ms: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a ThreeWidget.

        Args:
            data: Iterable of dicts with ``x``, ``y``, ``z`` coordinates and
                optional ``color``/``size`` keys.
            width: Canvas width in pixels.
            height: Canvas height in pixels.
            show_grid: Whether to show a grid helper.
            show_axes: Whether to show axis helpers.
            dark_mode: Whether to render with a dark background.
            axis_labels: Optional axis labels for x/y/z.
            animate_updates: Whether to animate point updates.
            animation_duration_ms: Animation duration in milliseconds.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(
            data=list(data) if data is not None else [],
            width=width,
            height=height,
            show_grid=show_grid,
            show_axes=show_axes,
            dark_mode=dark_mode,
            axis_labels=list(axis_labels) if axis_labels is not None else [],
            animate_updates=animate_updates,
            animation_duration_ms=animation_duration_ms,
            **kwargs,
        )

    def update_points(
        self,
        updates: Iterable[Mapping[str, Any]],
        *,
        animate: bool = False,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Update point properties in-place while preserving list length.

        Args:
            updates: Iterable of dict-like updates aligned with existing points.
                Each update can include any subset of ``x``, ``y``, ``z``,
                ``color``, ``size`` keys.
            animate: Whether to animate the transition.
            duration_ms: Optional animation duration override in milliseconds.
        """
        update_list = list(updates)
        if len(update_list) != len(self.data):
            raise ValueError(
                "updates must have the same length as the current data list."
            )
        merged: list[dict[str, Any]] = []
        for current, update in zip(self.data, update_list):
            if not isinstance(update, Mapping):
                raise TypeError("Each update must be a mapping of point properties.")
            next_point = dict(current)
            next_point.update(update)
            merged.append(next_point)
        if duration_ms is not None:
            self.animation_duration_ms = duration_ms
        self.animate_updates = animate
        self.data = merged
