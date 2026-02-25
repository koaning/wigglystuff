"""ChartMultiSelect widget for multi-region classification on matplotlib charts."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from anywidget import AnyWidget
import traitlets

from .chart_puck import extract_axes_info, fig_to_base64


class ChartMultiSelect(AnyWidget):
    """Multi-region selection overlay for matplotlib charts.

    Like ``ChartSelect`` but supports multiple persistent box/lasso selections,
    each tagged with a class label.  Draw regions for different classes, then
    use ``get_labels`` to classify points.

    Examples:
        Basic usage:

        ```python
        import matplotlib.pyplot as plt
        from wigglystuff import ChartMultiSelect

        fig, ax = plt.subplots()
        ax.scatter(x_data, y_data)

        ms = ChartMultiSelect(fig, n_classes=3)
        # ms.selections is a list of selection dicts
        # ms.get_labels(x_data, y_data) returns class labels
        ```

        Filtering by class:

        ```python
        labels = ms.get_labels(x_data, y_data)
        class_0 = x_data[labels == 0]
        ```
    """

    _esm = Path(__file__).parent / "static" / "chart-multi-select.js"
    _css = Path(__file__).parent / "static" / "chart-multi-select.css"

    # Selection mode: "box" or "lasso"
    mode = traitlets.Unicode("box").tag(sync=True)

    # Available modes (controls which buttons are shown)
    modes = traitlets.List(
        traitlets.Unicode(), default_value=["box", "lasso"]
    ).tag(sync=True)

    # Number of classes (1–4)
    n_classes = traitlets.Int(2).tag(sync=True)

    # Currently active class for the next drawn selection
    active_class = traitlets.Int(0).tag(sync=True)

    # All selections.  Each dict has:
    #   "type": "box" or "lasso"
    #   "class_id": int
    #   Box: "x_min", "y_min", "x_max", "y_max" (display space)
    #   Lasso: "vertices": [[x1, y1], [x2, y2], ...] (display space)
    selections = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)

    # Index of the currently highlighted (selected-for-editing) selection, -1 = none
    selected_index = traitlets.Int(-1).tag(sync=True)

    # Chart bounds in display space (log10 for log axes)
    x_bounds = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)
    y_bounds = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)

    # Axes position in pixels (for coordinate mapping)
    axes_pixel_bounds = traitlets.Tuple(
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        default_value=(0.0, 0.0, 100.0, 100.0),
    ).tag(sync=True)

    # Image dimensions and content
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    chart_base64 = traitlets.Unicode("").tag(sync=True)

    # Styling
    selection_opacity = traitlets.Float(0.3).tag(sync=True)
    stroke_width = traitlets.Int(2).tag(sync=True)

    def __init__(
        self,
        fig,
        n_classes: int = 2,
        mode: str = "box",
        modes: list[str] | None = None,
        selection_opacity: float = 0.3,
        **kwargs: Any,
    ) -> None:
        """Create a ChartMultiSelect widget from a matplotlib figure.

        Args:
            fig: A matplotlib figure to overlay selections on.
            n_classes: Number of class labels (1–4).
            mode: Selection mode (``"box"`` or ``"lasso"``).
            modes: Available modes. Defaults to ``["box", "lasso"]``.
            selection_opacity: Opacity of selection fill (0–1).
            **kwargs: Forwarded to ``AnyWidget``.
        """
        x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px, x_scale, y_scale = (
            extract_axes_info(fig)
        )
        chart_base64 = fig_to_base64(fig)

        self._x_scale = x_scale
        self._y_scale = y_scale

        if x_scale == "log":
            x_bounds = (math.log10(x_bounds[0]), math.log10(x_bounds[1]))
        if y_scale == "log":
            y_bounds = (math.log10(y_bounds[0]), math.log10(y_bounds[1]))

        if modes is None:
            modes = ["box", "lasso"]

        super().__init__(
            mode=mode,
            modes=modes,
            n_classes=n_classes,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            axes_pixel_bounds=axes_pixel_bounds,
            width=width_px,
            height=height_px,
            chart_base64=chart_base64,
            selection_opacity=selection_opacity,
            **kwargs,
        )

    @traitlets.validate("n_classes")
    def _validate_n_classes(self, proposal):
        value = proposal["value"]
        if not 1 <= value <= 4:
            raise traitlets.TraitError("n_classes must be between 1 and 4")
        return value

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _to_display(self, x, y):
        """Convert data-space coordinates to display space (log10 if needed)."""
        if self._x_scale == "log":
            x = math.log10(x)
        if self._y_scale == "log":
            y = math.log10(y)
        return x, y

    def _from_display(self, x, y):
        """Convert display-space coordinates back to data space."""
        if self._x_scale == "log":
            x = 10**x
        if self._y_scale == "log":
            y = 10**y
        return x, y

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all selections."""
        self.selections = []
        self.selected_index = -1

    @staticmethod
    def _selection_mask_display(sel, x_d, y_d):
        """Boolean mask for a single selection (display-space coords)."""
        import numpy as np

        if sel["type"] == "box":
            return (
                (x_d >= sel["x_min"])
                & (x_d <= sel["x_max"])
                & (y_d >= sel["y_min"])
                & (y_d <= sel["y_max"])
            )
        # lasso
        from matplotlib.path import Path as MplPath

        vertices = sel.get("vertices", [])
        if len(vertices) < 3:
            return np.zeros(len(x_d), dtype=bool)
        path = MplPath(vertices)
        return path.contains_points(np.column_stack([x_d, y_d]))

    def get_labels(self, x_arr, y_arr):
        """Return integer class labels for each point.

        Points not covered by any selection get ``-1``.  When selections
        overlap the last-drawn selection wins.

        Args:
            x_arr: Array-like of x coordinates (data space).
            y_arr: Array-like of y coordinates (data space).

        Returns:
            Numpy integer array of length ``len(x_arr)``.
        """
        import numpy as np

        x_arr = np.asarray(x_arr, dtype=float)
        y_arr = np.asarray(y_arr, dtype=float)
        labels = np.full(len(x_arr), -1, dtype=int)

        x_d = np.log10(x_arr) if self._x_scale == "log" else x_arr
        y_d = np.log10(y_arr) if self._y_scale == "log" else y_arr

        for sel in self.selections:
            mask = self._selection_mask_display(sel, x_d, y_d)
            labels[mask] = sel["class_id"]

        return labels

    def get_mask(self, x_arr, y_arr, class_id=None):
        """Boolean mask for classified points.

        Args:
            x_arr: Array-like of x coordinates.
            y_arr: Array-like of y coordinates.
            class_id: If ``None``, ``True`` for any classified point.
                      If an ``int``, ``True`` only for that class.

        Returns:
            Boolean numpy array.
        """
        labels = self.get_labels(x_arr, y_arr)
        if class_id is None:
            return labels >= 0
        return labels == class_id

    def get_indices(self, x_arr, y_arr, class_id=None):
        """Indices of classified points.

        Args:
            x_arr: Array-like of x coordinates.
            y_arr: Array-like of y coordinates.
            class_id: Optional class filter (see ``get_mask``).

        Returns:
            Numpy integer array of indices.
        """
        import numpy as np

        return np.where(self.get_mask(x_arr, y_arr, class_id))[0]

    # ------------------------------------------------------------------
    # from_callback
    # ------------------------------------------------------------------

    @classmethod
    def from_callback(
        cls,
        draw_fn,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
        figsize: tuple[float, float] = (6, 6),
        n_classes: int = 2,
        mode: str = "box",
        modes: list[str] | None = None,
        **kwargs: Any,
    ) -> "ChartMultiSelect":
        """Create a ChartMultiSelect that re-renders when selections change.

        Args:
            draw_fn: ``function(ax, widget)`` that draws onto the axes.
            x_bounds: Fixed (min, max) for x-axis.
            y_bounds: Fixed (min, max) for y-axis.
            figsize: Figure size in inches.
            n_classes: Number of class labels (1–4).
            mode: Initial selection mode.
            modes: Available modes.
            **kwargs: Passed to ``ChartMultiSelect``.

        Returns:
            A ``ChartMultiSelect`` with auto-update and ``redraw()``.
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)

        class _Proxy:
            def __init__(self):
                self.selections = []
                self.active_class = 0
                self.n_classes = n_classes

            def get_labels(self, x, y):
                import numpy as np
                return np.full(len(np.asarray(x)), -1, dtype=int)

            def get_mask(self, x, y, class_id=None):
                import numpy as np
                return np.zeros(len(np.asarray(x)), dtype=bool)

            def get_indices(self, x, y, class_id=None):
                import numpy as np
                return np.array([], dtype=int)

            def clear(self):
                pass

        draw_fn(ax, _Proxy())

        widget = cls(fig, n_classes=n_classes, mode=mode, modes=modes, **kwargs)

        def render():
            ax.clear()
            ax.set_xlim(x_bounds)
            ax.set_ylim(y_bounds)
            draw_fn(ax, widget)
            return fig_to_base64(fig)

        widget._render = render
        widget.chart_base64 = render()

        def on_change(change):
            widget.chart_base64 = render()

        widget.observe(on_change, names=["selections", "selected_index"])

        return widget

    def redraw(self) -> None:
        """Re-render the chart using the stored callback.

        Only available for widgets created via ``from_callback()``.
        """
        if hasattr(self, "_render"):
            self.chart_base64 = self._render()
