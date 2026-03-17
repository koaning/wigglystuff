# ChartMultiSelect API


 Bases: `AnyWidget`


Multi-region selection overlay for matplotlib charts.


Like `ChartSelect` but supports multiple persistent box/lasso selections, each tagged with a class label. Draw regions for different classes, then use `get_labels` to classify points.



Basic usage:


```
from wigglystuff import ChartMultiSelect

import matplotlib.pyplot as plt
from wigglystuff import ChartMultiSelect

fig, ax = plt.subplots()
ax.scatter(x_data, y_data)

ms = ChartMultiSelect(fig, n_classes=3)
# ms.selections is a list of selection dicts
# ms.get_labels(x_data, y_data) returns class labels
```


Filtering by class:


```
labels = ms.get_labels(x_data, y_data)
class_0 = x_data[labels == 0]
```


Create a ChartMultiSelect widget from a matplotlib figure.


  Source code in `wigglystuff/chart_multi_select.py`

```
def __init__(
    self,
    fig: Any,
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
```


## clear


```
clear() -> None
```


Remove all selections.

 Source code in `wigglystuff/chart_multi_select.py`

```
def clear(self) -> None:
    """Remove all selections."""
    self.selections = []
    self.selected_index = -1
```


## from_callback `classmethod`


```
from_callback(
    draw_fn: Callable[..., Any],
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    figsize: tuple[float, float] = (6, 6),
    n_classes: int = 2,
    mode: str = "box",
    modes: list[str] | None = None,
    **kwargs: Any
) -> "ChartMultiSelect"
```


Create a ChartMultiSelect that re-renders when selections change.




| Type | Description |
| --- | --- |
| `'ChartMultiSelect'` | A `ChartMultiSelect` with auto-update and `redraw()`. |

 Source code in `wigglystuff/chart_multi_select.py`

```
@classmethod
def from_callback(
    cls,
    draw_fn: Callable[..., Any],
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
```


## get_indices


```
get_indices(
    x_arr: Any, y_arr: Any, class_id: int | None = None
) -> "np.ndarray"
```


Indices of classified points.




| Type | Description |
| --- | --- |
| `'np.ndarray'` | Numpy integer array of indices. |

 Source code in `wigglystuff/chart_multi_select.py`

```
def get_indices(self, x_arr: Any, y_arr: Any, class_id: int | None = None) -> "np.ndarray":
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
```


## get_labels


```
get_labels(x_arr: Any, y_arr: Any) -> 'np.ndarray'
```


Return integer class labels for each point.


Points not covered by any selection get `-1`. When selections overlap the last-drawn selection wins.




| Type | Description |
| --- | --- |
| `'np.ndarray'` | Numpy integer array of length `len(x_arr)`. |

 Source code in `wigglystuff/chart_multi_select.py`

```
def get_labels(self, x_arr: Any, y_arr: Any) -> "np.ndarray":
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
```


## get_mask


```
get_mask(
    x_arr: Any, y_arr: Any, class_id: int | None = None
) -> "np.ndarray"
```


Boolean mask for classified points.




| Type | Description |
| --- | --- |
| `'np.ndarray'` | Boolean numpy array. |

 Source code in `wigglystuff/chart_multi_select.py`

```
def get_mask(self, x_arr: Any, y_arr: Any, class_id: int | None = None) -> "np.ndarray":
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
```


## redraw


```
redraw() -> None
```


Re-render the chart using the stored callback.


Only available for widgets created via `from_callback()`.

 Source code in `wigglystuff/chart_multi_select.py`

```
def redraw(self) -> None:
    """Re-render the chart using the stored callback.

    Only available for widgets created via ``from_callback()``.
    """
    if hasattr(self, "_render"):
        self.chart_base64 = self._render()
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `mode` | `str` | Selection mode: "box" or "lasso". |
| `modes` | `list[str]` | Available modes (controls which buttons are shown). |
| `n_classes` | `int` | Number of class labels (1–4). |
| `active_class` | `int` | Currently active class for the next drawn selection. |
| `selections` | `list[dict]` | All selections. Each dict has `type`, `class_id`, and geometry keys. |
| `selected_index` | `int` | Index of the highlighted selection (-1 = none). |
| `x_bounds` | `tuple[float, float]` | Min/max x-axis bounds from matplotlib. |
| `y_bounds` | `tuple[float, float]` | Min/max y-axis bounds from matplotlib. |
| `axes_pixel_bounds` | `tuple[float, float, float, float]` | Axes position in pixels (left, top, right, bottom). |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `chart_base64` | `str` | Base64-encoded PNG of the matplotlib figure. |
| `selection_opacity` | `float` | Opacity of selection fill (0-1). |
| `stroke_width` | `int` | Width of selection border in pixels. |


## Helper methods


| Method | Returns | Description |
| --- | --- | --- |
| `clear()` | `None` | Remove all selections. |
| `get_labels(x_arr, y_arr)` | `ndarray[int]` | Class labels per point (-1 = unclassified, last-drawn wins for overlap). |
| `get_mask(x_arr, y_arr, class_id=None)` | `ndarray[bool]` | Boolean mask for classified points (optionally filtered by class). |
| `get_indices(x_arr, y_arr, class_id=None)` | `ndarray[int]` | Indices of classified points. |
| `redraw()` | `None` | Re-render chart (only for `from_callback` widgets). |
