from pathlib import Path
from typing import Any, Iterable, Optional

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
            **kwargs,
        )
