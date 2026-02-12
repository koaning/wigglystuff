"""ChartSelect widget for region selection on matplotlib charts."""

from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from anywidget import AnyWidget
import traitlets

from .chart_puck import extract_axes_info, fig_to_base64


class ChartSelect(AnyWidget):
    """Region selection overlay for matplotlib charts.

    Allows interactive box or lasso (freehand) selection on a static matplotlib
    chart. Returns selection coordinates in data space for user-side filtering.

    Examples:
        Basic usage:

        ```python
        import matplotlib.pyplot as plt
        from wigglystuff import ChartSelect

        fig, ax = plt.subplots()
        ax.scatter(x_data, y_data)

        select = ChartSelect(fig)
        # select.selection contains the selection bounds/vertices
        # select.has_selection is True when a selection exists
        ```

        Filtering with a mask:

        ```python
        mask = select.get_mask(x_data, y_data)
        selected_x = x_data[mask]
        ```

        Filtering a DataFrame:

        ```python
        indices = select.get_indices(df["x"], df["y"])
        selected_df = df.iloc[indices]
        ```
    """

    _esm = Path(__file__).parent / "static" / "chart-select.js"
    _css = Path(__file__).parent / "static" / "chart-select.css"

    # Selection mode: "box" or "lasso"
    mode = traitlets.Unicode("box").tag(sync=True)

    # Available modes (controls which buttons are shown)
    modes = traitlets.List(
        traitlets.Unicode(), default_value=["box", "lasso"]
    ).tag(sync=True)

    # Selection data in display coordinates (log10 space for log axes)
    # For box: {"x_min": float, "y_min": float, "x_max": float, "y_max": float}
    # For lasso: {"vertices": [[x1, y1], [x2, y2], ...]}
    selection = traitlets.Dict(default_value={}).tag(sync=True)

    # Whether a selection is currently active
    has_selection = traitlets.Bool(False).tag(sync=True)

    # Chart bounds sent to JS (in display space: log10 for log axes)
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

    # Styling options
    selection_color = traitlets.Unicode("#3b82f6").tag(sync=True)
    selection_opacity = traitlets.Float(0.3).tag(sync=True)
    stroke_width = traitlets.Int(2).tag(sync=True)

    def __init__(
        self,
        fig,
        mode: str = "box",
        modes: list[str] | None = None,
        selection_color: str = "#3b82f6",
        selection_opacity: float = 0.3,
        **kwargs: Any,
    ) -> None:
        """Create a ChartSelect widget from a matplotlib figure.

        Args:
            fig: A matplotlib figure to overlay selection on.
            mode: Selection mode ("box" or "lasso").
            modes: List of available modes. Defaults to ["box", "lasso"].
                   Pass a single-item list to lock to one mode.
            selection_color: Fill color for selection region.
            selection_opacity: Opacity of selection fill (0-1).
            **kwargs: Forwarded to ``AnyWidget``.
        """
        x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px, x_scale, y_scale = extract_axes_info(
            fig
        )
        chart_base64 = fig_to_base64(fig)

        # Store scale types for coordinate transforms in helper methods
        self._x_scale = x_scale
        self._y_scale = y_scale

        # Send bounds in display space so JS can use plain linear math.
        # Using log10 is correct for any log base because the base cancels
        # out in the fractional position: log_b(x)/log_b(max) == log10(x)/log10(max).
        if x_scale == "log":
            x_bounds = (math.log10(x_bounds[0]), math.log10(x_bounds[1]))
        if y_scale == "log":
            y_bounds = (math.log10(y_bounds[0]), math.log10(y_bounds[1]))

        if modes is None:
            modes = ["box", "lasso"]

        super().__init__(
            mode=mode,
            modes=modes,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            axes_pixel_bounds=axes_pixel_bounds,
            width=width_px,
            height=height_px,
            chart_base64=chart_base64,
            selection_color=selection_color,
            selection_opacity=selection_opacity,
            **kwargs,
        )

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
            x = 10 ** x
        if self._y_scale == "log":
            y = 10 ** y
        return x, y

    def clear(self) -> None:
        """Clear the current selection."""
        self.selection = {}
        self.has_selection = False

    def _is_box_selection(self) -> bool:
        """Check if current selection is box format (vs lasso/polygon)."""
        return "x_min" in self.selection

    def get_bounds(self) -> tuple[float, float, float, float] | None:
        """Get bounding box of selection in data coordinates.

        Returns:
            (x_min, y_min, x_max, y_max) or None if no selection.
        """
        if not self.has_selection or not self.selection:
            return None

        if self._is_box_selection():
            x_min = self.selection["x_min"]
            y_min = self.selection["y_min"]
            x_max = self.selection["x_max"]
            y_max = self.selection["y_max"]
        else:  # lasso or polygon
            vertices = self.selection.get("vertices", [])
            if not vertices:
                return None
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

        # Transform back from display space to data space
        x_min, y_min = self._from_display(x_min, y_min)
        x_max, y_max = self._from_display(x_max, y_max)
        return (x_min, y_min, x_max, y_max)

    def get_vertices(self) -> list[tuple[float, float]]:
        """Get selection vertices in data coordinates.

        For box mode, returns the 4 corners (clockwise from bottom-left).
        For lasso mode, returns the path vertices.

        Returns:
            List of (x, y) tuples, or empty list if no selection.
        """
        if not self.has_selection or not self.selection:
            return []

        if self._is_box_selection():
            x_min = self.selection["x_min"]
            y_min = self.selection["y_min"]
            x_max = self.selection["x_max"]
            y_max = self.selection["y_max"]
            verts = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        else:
            verts = [tuple(v) for v in self.selection.get("vertices", [])]

        return [self._from_display(x, y) for x, y in verts]

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the selection region.

        Uses matplotlib's Path.contains_point for lasso selections.

        Args:
            x: X coordinate in data space.
            y: Y coordinate in data space.

        Returns:
            True if the point is inside the selection, False otherwise.
        """
        if not self.has_selection:
            return False

        # Work in display space (where the selection lives)
        xd, yd = self._to_display(x, y)

        if self._is_box_selection():
            s = self.selection
            return s["x_min"] <= xd <= s["x_max"] and s["y_min"] <= yd <= s["y_max"]
        else:
            from matplotlib.path import Path as MplPath

            vertices = self.selection.get("vertices", [])
            if len(vertices) < 3:
                return False
            path = MplPath(vertices)
            return path.contains_point((xd, yd))

    def get_mask(self, x_arr, y_arr):
        """Return boolean mask for points inside the selection.

        Args:
            x_arr: Array-like of x coordinates.
            y_arr: Array-like of y coordinates.

        Returns:
            Boolean numpy array where True means point is inside selection.
        """
        import numpy as np

        x_arr = np.asarray(x_arr, dtype=float)
        y_arr = np.asarray(y_arr, dtype=float)

        if not self.has_selection:
            return np.zeros(len(x_arr), dtype=bool)

        # Transform input data to display space for comparison
        x_d = np.log10(x_arr) if self._x_scale == "log" else x_arr
        y_d = np.log10(y_arr) if self._y_scale == "log" else y_arr

        if self._is_box_selection():
            s = self.selection
            return (
                (x_d >= s["x_min"])
                & (x_d <= s["x_max"])
                & (y_d >= s["y_min"])
                & (y_d <= s["y_max"])
            )
        else:
            from matplotlib.path import Path as MplPath

            vertices = self.selection.get("vertices", [])
            if len(vertices) < 3:
                return np.zeros(len(x_arr), dtype=bool)
            path = MplPath(vertices)
            points = np.column_stack([x_d, y_d])
            return path.contains_points(points)

    def get_indices(self, x_arr, y_arr):
        """Return indices of points inside the selection.

        Useful for filtering dataframes with ``df.iloc[indices]``.

        Args:
            x_arr: Array-like of x coordinates.
            y_arr: Array-like of y coordinates.

        Returns:
            Numpy array of integer indices for points inside the selection.
        """
        import numpy as np

        return np.where(self.get_mask(x_arr, y_arr))[0]

    @classmethod
    def from_callback(
        cls,
        draw_fn,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
        figsize: tuple[float, float] = (6, 6),
        mode: str = "box",
        modes: list[str] | None = None,
        **kwargs: Any,
    ) -> "ChartSelect":
        """Create a ChartSelect that auto-updates when selection changes.

        The callback function is called on init and whenever the selection
        changes. Use ``redraw()`` to manually trigger a re-render.

        Args:
            draw_fn: A function(ax, widget) that draws onto the axes.
                     Receives the axes and the widget instance, allowing access
                     to widget.selection and widget.has_selection.
                     The axes is pre-cleared and bounds are pre-set.
            x_bounds: (min, max) for x-axis - fixed for lifetime of widget.
            y_bounds: (min, max) for y-axis - fixed for lifetime of widget.
            figsize: Figure size in inches.
            mode: Selection mode ("box" or "lasso").
            modes: List of available modes. Defaults to ["box", "lasso"].
            **kwargs: Passed to ChartSelect (selection_color, etc.)

        Returns:
            A ChartSelect instance with auto-update behavior and redraw() method.

        Examples:
            ```python
            def draw_chart(ax, widget):
                ax.scatter(data_x, data_y, alpha=0.6)
                if widget.has_selection:
                    idx = widget.get_indices(data_x, data_y)
                    ax.scatter(data_x[idx], data_y[idx], color='red')

            select = ChartSelect.from_callback(
                draw_fn=draw_chart,
                x_bounds=(-3, 3),
                y_bounds=(-3, 3),
            )
            ```
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)

        # Preliminary render so draw_fn can configure axes (e.g. log scale)
        _stub = SimpleNamespace(has_selection=False, selection={})
        draw_fn(ax, _stub)

        widget = cls(fig, mode=mode, modes=modes, **kwargs)

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

        widget.observe(on_change, names=["selection", "has_selection"])

        return widget

    def redraw(self) -> None:
        """Re-render the chart using the stored callback.

        Only available for widgets created via ``from_callback()``. Call this
        when external state that affects the chart has changed.
        """
        if hasattr(self, "_render"):
            self.chart_base64 = self._render()
