# ChartSelect API

::: wigglystuff.chart_select.ChartSelect

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `mode` | `str` | Selection mode: "box" or "lasso". |
| `modes` | `list[str]` | Available modes (controls which buttons are shown). |
| `selection` | `dict` | Selection data in data coordinates. Box: `{x_min, y_min, x_max, y_max}`. Lasso: `{vertices: [[x, y], ...]}`. |
| `has_selection` | `bool` | Whether a selection is currently active. |
| `x_bounds` | `tuple[float, float]` | Min/max x-axis bounds from matplotlib. |
| `y_bounds` | `tuple[float, float]` | Min/max y-axis bounds from matplotlib. |
| `axes_pixel_bounds` | `tuple[float, float, float, float]` | Axes position in pixels (left, top, right, bottom). |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `chart_base64` | `str` | Base64-encoded PNG of the matplotlib figure. |
| `selection_color` | `str` | CSS color for selection fill and stroke. |
| `selection_opacity` | `float` | Opacity of selection fill (0-1). |
| `stroke_width` | `int` | Width of selection border in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `clear()` | `None` | Clear the current selection. |
| `get_bounds()` | `tuple` or `None` | Bounding box `(x_min, y_min, x_max, y_max)` in data coordinates. |
| `get_vertices()` | `list[tuple]` | Selection vertices as `(x, y)` tuples. |
| `contains_point(x, y)` | `bool` | Check if a point is inside the selection. |
| `get_mask(x_arr, y_arr)` | `ndarray[bool]` | Boolean mask for points inside selection. |
| `get_indices(x_arr, y_arr)` | `ndarray[int]` | Indices of points inside selection. |
| `redraw()` | `None` | Re-render chart (only for `from_callback` widgets). |
