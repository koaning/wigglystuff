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
| `brush_extents` | `dict` | Current brush ranges on axes. Resets to `{}` after Keep/Exclude. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |

## Methods

| Method | Description |
| --- | --- |
| `selections` | Property returning `filter_history` + a trailing `{"action": "current", "extents": ...}` entry for the active brush (if any). |
| `keep()` | Trigger a Keep action on the current brush selection (same as the Keep button). |
| `exclude()` | Trigger an Exclude action on the current brush selection (same as the Exclude button). |
| `restore()` | Restore all rows and clear `filter_history` (same as the Restore button). |
| `filtered_data` | Property returning the list of dicts for rows passing all filters. |
| `filtered_as_pandas` | Property returning filtered data as a pandas DataFrame. |
| `filtered_as_polars` | Property returning filtered data as a polars DataFrame. |
| `selected_data` | Property returning the list of dicts for selected rows. |
