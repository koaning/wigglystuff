# ParallelCoordinates API

::: wigglystuff.parallel_coords.ParallelCoordinates

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | Input rows rendered as polylines. |
| `color_by` | `str` | Column used for line coloring. |
| `color_map` | `dict` | Map of categorical values to CSS colors (e.g. `{"a": "red", "b": "#00f"}`). Unmapped values use the default palette. |
| `height` | `int` | Plot height in pixels. |
| `width` | `int` | Plot width in pixels. Set to 0 for container width. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |
