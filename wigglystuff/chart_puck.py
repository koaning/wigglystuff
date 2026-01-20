"""ChartPuck widget for overlaying draggable pucks on matplotlib charts."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any

import anywidget
import traitlets


def fig_to_base64(fig) -> str:
    """Render matplotlib figure to base64 PNG."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def extract_axes_info(fig):
    """Extract axes bounds and pixel position from a matplotlib figure.

    Returns:
        tuple: (x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px)
    """
    fig.canvas.draw()
    ax = fig.axes[0]

    x_bounds = ax.get_xlim()
    y_bounds = ax.get_ylim()

    bbox = ax.get_position()
    width_px = int(fig.get_figwidth() * fig.dpi)
    height_px = int(fig.get_figheight() * fig.dpi)

    # Convert to pixel coords (flip Y for top-left origin)
    left = bbox.x0 * width_px
    right = (bbox.x0 + bbox.width) * width_px
    top = (1 - bbox.y0 - bbox.height) * height_px
    bottom = (1 - bbox.y0) * height_px

    return x_bounds, y_bounds, (left, top, right, bottom), width_px, height_px


class ChartPuck(anywidget.AnyWidget):
    """Draggable puck overlay for matplotlib charts.

    Allows interactive selection of coordinates on a static matplotlib chart.
    Supports single or multiple pucks. The puck positions are tracked in data
    coordinates.

    Examples:
        Single puck:
        ```python
        import matplotlib.pyplot as plt
        from wigglystuff import ChartPuck

        fig, ax = plt.subplots()
        ax.scatter([1, 2, 3], [1, 2, 3])

        puck = ChartPuck(fig)
        # puck.x, puck.y track the puck position in data coordinates
        ```

        Multiple pucks:
        ```python
        puck = ChartPuck(fig, x=[0.5, 1.5, 2.5], y=[0.5, 1.5, 2.5])
        # puck.x, puck.y are lists of coordinates
        ```
    """

    _esm = Path(__file__).parent / "static" / "chart-puck.js"

    # Puck positions in data coordinates (synced to Python)
    # Always stored as lists internally
    x = traitlets.List(traitlets.Float(), default_value=[0.0]).tag(sync=True)
    y = traitlets.List(traitlets.Float(), default_value=[0.0]).tag(sync=True)

    # Bounds from matplotlib axes (auto-extracted)
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

    # Puck styling
    puck_radius = traitlets.Int(10).tag(sync=True)
    puck_color = traitlets.Unicode("#e63946").tag(sync=True)

    def __init__(
        self,
        fig,
        x: float | list[float] | None = None,
        y: float | list[float] | None = None,
        puck_radius: int = 10,
        puck_color: str = "#e63946",
        **kwargs: Any,
    ) -> None:
        """Create a ChartPuck widget from a matplotlib figure.

        Args:
            fig: A matplotlib figure to overlay the puck on.
            x: Initial x coordinate(s) in data space. Can be a single value or
               a list for multiple pucks. Defaults to center of x_bounds.
            y: Initial y coordinate(s) in data space. Can be a single value or
               a list for multiple pucks. Defaults to center of y_bounds.
            puck_radius: Radius of the puck(s) in pixels.
            puck_color: Color of the puck(s) (any CSS color).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px = extract_axes_info(
            fig
        )
        chart_base64 = fig_to_base64(fig)

        # Default to center of bounds if not specified
        center_x = (x_bounds[0] + x_bounds[1]) / 2
        center_y = (y_bounds[0] + y_bounds[1]) / 2

        # Normalize to lists
        if x is None:
            x = [center_x]
        elif not isinstance(x, list):
            x = [x]

        if y is None:
            y = [center_y]
        elif not isinstance(y, list):
            y = [y]

        if len(x) != len(y):
            raise ValueError(
                f"x and y must have the same length, got {len(x)} and {len(y)}"
            )

        super().__init__(
            x=x,
            y=y,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            axes_pixel_bounds=axes_pixel_bounds,
            width=width_px,
            height=height_px,
            chart_base64=chart_base64,
            puck_radius=puck_radius,
            puck_color=puck_color,
            **kwargs,
        )

    @classmethod
    def from_callback(
        cls,
        draw_fn,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
        figsize: tuple[float, float] = (6, 6),
        x: float | list[float] | None = None,
        y: float | list[float] | None = None,
        **kwargs: Any,
    ) -> "ChartPuck":
        """Create a ChartPuck that auto-updates when the puck moves.

        This is the recommended way to create a ChartPuck when you want the chart
        to update dynamically as the puck is dragged. The callback function is
        called on init and whenever the puck position changes.

        Args:
            draw_fn: A function(ax, x, y) that draws onto the axes.
                     Called on init and whenever puck position changes.
                     The axes is pre-cleared and bounds are pre-set.
            x_bounds: (min, max) for x-axis - fixed for lifetime of widget.
            y_bounds: (min, max) for y-axis - fixed for lifetime of widget.
            figsize: Figure size in inches.
            x: Initial x position(s). Defaults to center of x_bounds.
            y: Initial y position(s). Defaults to center of y_bounds.
            **kwargs: Passed to ChartPuck (puck_radius, puck_color, etc.)

        Returns:
            A ChartPuck instance with auto-update behavior.

        Examples:
            ```python
            def draw_chart(ax, x, y):
                ax.scatter(data_x, data_y, alpha=0.6)
                ax.axvline(x, color='red', linestyle='--')
                ax.axhline(y, color='red', linestyle='--')

            puck = ChartPuck.from_callback(
                draw_fn=draw_chart,
                x_bounds=(-3, 3),
                y_bounds=(-3, 3),
                figsize=(6, 6),
                x=0, y=0
            )
            ```
        """
        import matplotlib.pyplot as plt

        # Default to center of bounds if not specified
        if x is None:
            x = (x_bounds[0] + x_bounds[1]) / 2
        if y is None:
            y = (y_bounds[0] + y_bounds[1]) / 2

        # Normalize to lists
        x_list = x if isinstance(x, list) else [x]
        y_list = y if isinstance(y, list) else [y]

        # Create figure (owned by this closure)
        fig, ax = plt.subplots(figsize=figsize)

        def render(x_vals, y_vals):
            ax.clear()
            ax.set_xlim(x_bounds)
            ax.set_ylim(y_bounds)
            # Call user's draw function with first puck position
            draw_fn(ax, x_vals[0], y_vals[0])
            return fig_to_base64(fig)

        # Initial render
        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)
        draw_fn(ax, x_list[0], y_list[0])

        # Create widget
        widget = cls(fig, x=x, y=y, **kwargs)

        # Wire up observer for auto-updates
        def on_change(change):
            widget.chart_base64 = render(widget.x, widget.y)

        widget.observe(on_change, names=["x", "y"])

        return widget
