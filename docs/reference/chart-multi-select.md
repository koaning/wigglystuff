# ChartMultiSelect API

::: wigglystuff.chart_multi_select.ChartMultiSelect

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
