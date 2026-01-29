"""ChartSelect widget for region selection on matplotlib charts."""

from __future__ import annotations

from pathlib import Path
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

    # Selection data in data coordinates
    # For box: {"x_min": float, "y_min": float, "x_max": float, "y_max": float}
    # For lasso: {"vertices": [[x1, y1], [x2, y2], ...]}
    selection = traitlets.Dict(default_value={}).tag(sync=True)

    # Whether a selection is currently active
    has_selection = traitlets.Bool(False).tag(sync=True)

    # Chart bounds from matplotlib axes (auto-extracted)
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
        x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px = extract_axes_info(
            fig
        )
        chart_base64 = fig_to_base64(fig)

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

    def clear(self) -> None:
        """Clear the current selection."""
        self.selection = {}
        self.has_selection = False

    def get_bounds(self) -> tuple[float, float, float, float] | None:
        """Get bounding box of selection in data coordinates.

        Returns:
            (x_min, y_min, x_max, y_max) or None if no selection.
        """
        if not self.has_selection or not self.selection:
            return None

        if self.mode == "box":
            return (
                self.selection["x_min"],
                self.selection["y_min"],
                self.selection["x_max"],
                self.selection["y_max"],
            )
        else:  # lasso or polygon
            vertices = self.selection.get("vertices", [])
            if not vertices:
                return None
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            return (min(xs), min(ys), max(xs), max(ys))

    def get_vertices(self) -> list[tuple[float, float]]:
        """Get selection vertices in data coordinates.

        For box mode, returns the 4 corners (clockwise from bottom-left).
        For lasso mode, returns the path vertices.

        Returns:
            List of (x, y) tuples, or empty list if no selection.
        """
        if not self.has_selection or not self.selection:
            return []

        if self.mode == "box":
            x_min = self.selection["x_min"]
            y_min = self.selection["y_min"]
            x_max = self.selection["x_max"]
            y_max = self.selection["y_max"]
            return [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        else:
            return [tuple(v) for v in self.selection.get("vertices", [])]

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

        if self.mode == "box":
            bounds = self.get_bounds()
            if not bounds:
                return False
            return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]
        else:
            from matplotlib.path import Path

            vertices = self.get_vertices()
            if len(vertices) < 3:
                return False
            path = Path(vertices)
            return path.contains_point((x, y))

    def get_mask(self, x_arr, y_arr):
        """Return boolean mask for points inside the selection.

        Args:
            x_arr: Array-like of x coordinates.
            y_arr: Array-like of y coordinates.

        Returns:
            Boolean numpy array where True means point is inside selection.
        """
        import numpy as np

        x_arr = np.asarray(x_arr)
        y_arr = np.asarray(y_arr)

        if not self.has_selection:
            return np.zeros(len(x_arr), dtype=bool)

        if self.mode == "box":
            bounds = self.get_bounds()
            if not bounds:
                return np.zeros(len(x_arr), dtype=bool)
            return (
                (x_arr >= bounds[0])
                & (x_arr <= bounds[2])
                & (y_arr >= bounds[1])
                & (y_arr <= bounds[3])
            )
        else:
            from matplotlib.path import Path

            vertices = self.get_vertices()
            if len(vertices) < 3:
                return np.zeros(len(x_arr), dtype=bool)
            path = Path(vertices)
            points = np.column_stack([x_arr, y_arr])
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
