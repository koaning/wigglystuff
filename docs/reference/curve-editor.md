# CurveEditor API

::: wigglystuff.curve_editor.CurveEditor

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `points` | `list[dict]` | Chart knots as `{"x": float, "y": float}` in data coordinates. Open curves store points sorted by x-coordinate; closed curves preserve drawing order. |
| `x` | `float` | Current rendered path x-coordinate at `t`. |
| `y` | `float` | Current rendered path y-coordinate at `t`. |
| `t` | `float` | Path progress, clamped to `[0, 1]`. |
| `curve` | `str` | One of `linear`, `step`, `step_before`, `step_after`, `basis`, `natural`, `cardinal`, `catmull_rom`, `monotone_x`, or `bump_x`. |
| `tension` | `float` | Cardinal curve tension, clamped to `[0, 1]`. |
| `alpha` | `float` | Catmull-Rom alpha, clamped to `[0, 1]`. |
| `closed` | `bool` | Whether to virtually append the first point so the path returns to the start. |
| `playing` | `bool` | Whether playback is currently advancing `t`. |
| `loop` | `bool` | Whether playback wraps from `t=1` to `t=0`. |
| `interval_ms` | `int` | Milliseconds between browser playback ticks. |
| `duration_ms` | `int` | Milliseconds for one full `t=0` to `t=1` traversal. |
| `sync_throttle_ms` | `int` | Minimum milliseconds between playback updates synced to Python. |
| `selected_index` | `int` | Selected point index, or `-1` when no point is selected. |
| `x_bounds` | `tuple[float, float]` | Data-coordinate x bounds. |
| `y_bounds` | `tuple[float, float]` | Data-coordinate y bounds. |
| `width` | `int` | SVG width in pixels. |
| `height` | `int` | SVG height in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `current_point()` | `tuple[float, float]` | Current path progress point. In Python this is a linear knot approximation; the browser syncs from the actual rendered D3 path. |
