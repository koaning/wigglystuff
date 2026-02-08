# ChartPuck API


 Bases: `AnyWidget`


Draggable puck overlay for matplotlib charts.


Allows interactive selection of coordinates on a static matplotlib chart. Supports single or multiple pucks. The puck positions are tracked in data coordinates.



Single puck:

```
from wigglystuff import ChartPuck

import matplotlib.pyplot as plt
from wigglystuff import ChartPuck

fig, ax = plt.subplots()
ax.scatter([1, 2, 3], [1, 2, 3])

puck = ChartPuck(fig)
# puck.x, puck.y track the puck position in data coordinates
```


Multiple pucks:

```
puck = ChartPuck(fig, x=[0.5, 1.5, 2.5], y=[0.5, 1.5, 2.5])
# puck.x, puck.y are lists of coordinates
```


Create a ChartPuck widget from a matplotlib figure.


  Source code in `wigglystuff/chart_puck.py`

```
def __init__(
    self,
    fig,
    x: float | list[float] | None = None,
    y: float | list[float] | None = None,
    puck_radius: int = 10,
    puck_color: str | list[str] = "#e63946",
    throttle: int | str = 0,
    drag_x_bounds: tuple[float, float] | None = None,
    drag_y_bounds: tuple[float, float] | None = None,
) -> None:
    """Create a ChartPuck widget from a matplotlib figure.

    Args:
        fig: A matplotlib figure to overlay the puck on.
        x: Initial x coordinate(s) in data space. Can be a single value or
           a list for multiple pucks. Defaults to center of x_bounds.
        y: Initial y coordinate(s) in data space. Can be a single value or
           a list for multiple pucks. Defaults to center of y_bounds.
        puck_radius: Radius of the puck(s) in pixels.
        puck_color: Color of the puck(s). A single CSS color string applies
            to all pucks. A list of CSS colors assigns one color per puck
            (cycled if shorter than the number of pucks).
        throttle: Controls how often puck position syncs to Python during
            drag. ``0`` syncs on every mouse move (default). An integer
            syncs at most once every N milliseconds. ``"dragend"`` syncs
            only when the user releases the puck.
        drag_x_bounds: Optional (min, max) to constrain puck dragging on x-axis.
                      If None, uses the chart's x_bounds.
        drag_y_bounds: Optional (min, max) to constrain puck dragging on y-axis.
                      If None, uses the chart's y_bounds.
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

    # Normalize puck_color to list
    if isinstance(puck_color, str):
        puck_color = [puck_color]

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
        throttle=throttle,
        drag_x_bounds=drag_x_bounds,
        drag_y_bounds=drag_y_bounds,
    )
```


## export_kmeans


```
export_kmeans(
    n_init: int = 1, max_iter: int = 300, **kwargs
)
```


Export puck positions as a KMeans estimator with pucks as initial centroids.


Creates a scikit-learn KMeans instance configured to use the current puck positions as initial cluster centers. Useful for interactive clustering where you manually position pucks to define cluster centers.




| Type | Description |
| --- | --- |
|  | A sklearn.cluster.KMeans instance ready to fit on data. |



```
from wigglystuff import ChartPuck

puck = ChartPuck(fig, x=[1.0, 3.0], y=[1.0, 3.0])
# ... user drags pucks to desired positions ...

kmeans = puck.export_kmeans()
labels = kmeans.fit_predict(data)
```

 Source code in `wigglystuff/chart_puck.py`

```
def export_kmeans(self, n_init: int = 1, max_iter: int = 300, **kwargs):
    """Export puck positions as a KMeans estimator with pucks as initial centroids.

    Creates a scikit-learn KMeans instance configured to use the current puck
    positions as initial cluster centers. Useful for interactive clustering
    where you manually position pucks to define cluster centers.

    Args:
        n_init: Number of initializations. Defaults to 1 since we're providing
                explicit initial centers.
        max_iter: Maximum iterations for the algorithm.
        **kwargs: Additional arguments passed to sklearn.cluster.KMeans.

    Returns:
        A sklearn.cluster.KMeans instance ready to fit on data.

    Examples:
        ```python
        puck = ChartPuck(fig, x=[1.0, 3.0], y=[1.0, 3.0])
        # ... user drags pucks to desired positions ...

        kmeans = puck.export_kmeans()
        labels = kmeans.fit_predict(data)
        ```
    """
    import numpy as np
    from sklearn.cluster import KMeans

    centroids = np.array(list(zip(self.x, self.y)))
    return KMeans(
        n_clusters=len(self.x),
        init=centroids,
        n_init=n_init,
        max_iter=max_iter,
        **kwargs,
    )
```


## from_callback `classmethod`


```
from_callback(
    draw_fn,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    figsize: tuple[float, float] = (6, 6),
    x: float | list[float] | None = None,
    y: float | list[float] | None = None,
    drag_x_bounds: tuple[float, float] | None = None,
    drag_y_bounds: tuple[float, float] | None = None,
    **kwargs: Any
) -> "ChartPuck"
```


Create a ChartPuck that auto-updates when the puck moves.


This is the recommended way to create a ChartPuck when you want the chart to update dynamically as the puck is dragged. The callback function is called on init and whenever the puck position changes. Use `redraw()` to manually trigger a re-render (e.g., when external state changes).




| Type | Description |
| --- | --- |
| `'ChartPuck'` | A ChartPuck instance with auto-update behavior and redraw() method. |



```
from wigglystuff import ChartPuck

def draw_chart(ax, widget):
    ax.scatter(data_x, data_y, alpha=0.6)
    ax.axvline(widget.x[0], color='red', linestyle='--')
    ax.axhline(widget.y[0], color='red', linestyle='--')

puck = ChartPuck.from_callback(
    draw_fn=draw_chart,
    x_bounds=(-3, 3),
    y_bounds=(-3, 3),
    figsize=(6, 6),
    x=0, y=0
)

# Manually trigger redraw (e.g., when external state changes)
puck.redraw()
```

 Source code in `wigglystuff/chart_puck.py`

```
@classmethod
def from_callback(
    cls,
    draw_fn,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    figsize: tuple[float, float] = (6, 6),
    x: float | list[float] | None = None,
    y: float | list[float] | None = None,
    drag_x_bounds: tuple[float, float] | None = None,
    drag_y_bounds: tuple[float, float] | None = None,
    **kwargs: Any,
) -> "ChartPuck":
    """Create a ChartPuck that auto-updates when the puck moves.

    This is the recommended way to create a ChartPuck when you want the chart
    to update dynamically as the puck is dragged. The callback function is
    called on init and whenever the puck position changes. Use ``redraw()``
    to manually trigger a re-render (e.g., when external state changes).

    Args:
        draw_fn: A function(ax, widget) that draws onto the axes.
                 Receives the axes and the widget instance, allowing access
                 to widget.x and widget.y (lists of all puck positions).
                 Called on init and whenever puck position changes.
                 The axes is pre-cleared and bounds are pre-set.
        x_bounds: (min, max) for x-axis - fixed for lifetime of widget.
        y_bounds: (min, max) for y-axis - fixed for lifetime of widget.
        figsize: Figure size in inches.
        x: Initial x position(s). Defaults to center of x_bounds.
        y: Initial y position(s). Defaults to center of y_bounds.
        drag_x_bounds: Optional (min, max) to constrain puck dragging on x-axis.
        drag_y_bounds: Optional (min, max) to constrain puck dragging on y-axis.
        **kwargs: Passed to ChartPuck (puck_radius, puck_color, etc.)

    Returns:
        A ChartPuck instance with auto-update behavior and redraw() method.

    Examples:
        ```python
        def draw_chart(ax, widget):
            ax.scatter(data_x, data_y, alpha=0.6)
            ax.axvline(widget.x[0], color='red', linestyle='--')
            ax.axhline(widget.y[0], color='red', linestyle='--')

        puck = ChartPuck.from_callback(
            draw_fn=draw_chart,
            x_bounds=(-3, 3),
            y_bounds=(-3, 3),
            figsize=(6, 6),
            x=0, y=0
        )

        # Manually trigger redraw (e.g., when external state changes)
        puck.redraw()
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

    # Create widget first so render() can reference it
    # Initial render happens below after widget exists
    ax.set_xlim(x_bounds)
    ax.set_ylim(y_bounds)
    widget = cls(fig, x=x, y=y, drag_x_bounds=drag_x_bounds, drag_y_bounds=drag_y_bounds, **kwargs)

    def render():
        ax.clear()
        ax.set_xlim(x_bounds)
        ax.set_ylim(y_bounds)
        draw_fn(ax, widget)
        return fig_to_base64(fig)

    # Store render for redraw() method
    widget._render = render

    # Initial render with widget
    widget.chart_base64 = render()

    # Wire up observer for auto-updates
    def on_change(change):
        widget.chart_base64 = render()

    widget.observe(on_change, names=["x", "y"])

    return widget
```


## redraw


```
redraw() -> None
```


Re-render the chart using the stored callback.


Only available for widgets created via `from_callback()`. Call this when external state that affects the chart has changed (e.g., a dropdown selection) to trigger a re-render without moving the pucks.

 Source code in `wigglystuff/chart_puck.py`

```
def redraw(self) -> None:
    """Re-render the chart using the stored callback.

    Only available for widgets created via ``from_callback()``. Call this
    when external state that affects the chart has changed (e.g., a dropdown
    selection) to trigger a re-render without moving the pucks.
    """
    if hasattr(self, "_render"):
        self.chart_base64 = self._render()
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `x` | `list[float]` | Puck x-coordinates in data space. |
| `y` | `list[float]` | Puck y-coordinates in data space. |
| `x_bounds` | `tuple[float, float]` | Min/max x-axis bounds from matplotlib. |
| `y_bounds` | `tuple[float, float]` | Min/max y-axis bounds from matplotlib. |
| `axes_pixel_bounds` | `tuple[float, float, float, float]` | Axes position in pixels (left, top, right, bottom). |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `chart_base64` | `str` | Base64-encoded PNG of the matplotlib figure. |
| `puck_radius` | `int` | Radius of puck(s) in pixels. |
| `puck_color` | `str \\| list[str]` | CSS color(s) of puck(s). A single color applies to all; a list assigns one per puck. |
| `throttle` | `int \\| str` | Drag sync rate. `0` = every move, int = ms throttle, `"dragend"` = on release. |
