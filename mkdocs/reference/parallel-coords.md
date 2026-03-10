# ParallelCoordinates API

::: wigglystuff.parallel_coords.ParallelCoordinates

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | Input rows rendered as polylines. |
| `color_by` | `str` | Column used for line coloring. |
| `height` | `int` | Plot height in pixels. |
| `width` | `int` | Plot width in pixels. Set to 0 for container width. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |
