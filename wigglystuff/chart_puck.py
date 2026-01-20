"""ChartPuck widget for overlaying a draggable puck on matplotlib charts."""

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
    The puck position is tracked in data coordinates.

    Examples:
        ```python
        import matplotlib.pyplot as plt
        from wigglystuff import ChartPuck

        fig, ax = plt.subplots()
        ax.scatter([1, 2, 3], [1, 2, 3])

        puck = ChartPuck(fig)
        # puck.x, puck.y now track the puck position in data coordinates
        ```
    """

    _esm = Path(__file__).parent / "static" / "chart-puck.js"

    # Puck position in data coordinates (synced to Python)
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)

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
        x: float | None = None,
        y: float | None = None,
        puck_radius: int = 10,
        puck_color: str = "#e63946",
        **kwargs: Any,
    ) -> None:
        """Create a ChartPuck widget from a matplotlib figure.

        Args:
            fig: A matplotlib figure to overlay the puck on.
            x: Initial x coordinate in data space. Defaults to center of x_bounds.
            y: Initial y coordinate in data space. Defaults to center of y_bounds.
            puck_radius: Radius of the puck in pixels.
            puck_color: Color of the puck (any CSS color).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px = extract_axes_info(
            fig
        )
        chart_base64 = fig_to_base64(fig)

        # Default to center of bounds if not specified
        if x is None:
            x = (x_bounds[0] + x_bounds[1]) / 2
        if y is None:
            y = (y_bounds[0] + y_bounds[1]) / 2

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
