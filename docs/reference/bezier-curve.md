# BezierCurve API

::: wigglystuff.bezier_curve.BezierCurve

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `points` | `list[dict]` | Control points as `{"x": float, "y": float}` in data coordinates. |
| `x` | `float` | Current Bezier point x-coordinate at `t`. |
| `y` | `float` | Current Bezier point y-coordinate at `t`. |
| `t` | `float` | Curve parameter, clamped to `[0, 1]`. |
| `closed` | `bool` | Whether to virtually append the first point so the curve returns to the start. |
| `playing` | `bool` | Whether playback is currently advancing `t`. |
| `loop` | `bool` | Whether playback wraps from `t=1` to `t=0`. |
| `interval_ms` | `int` | Milliseconds between browser playback ticks. |
| `duration_ms` | `int` | Milliseconds for one full `t=0` to `t=1` traversal. |
| `sync_throttle_ms` | `int` | Minimum milliseconds between playback updates synced to Python. |
| `x_bounds` | `tuple[float, float]` | Data-coordinate x bounds. |
| `y_bounds` | `tuple[float, float]` | Data-coordinate y bounds. |
| `width` | `int` | SVG width in pixels. |
| `height` | `int` | SVG height in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `current_point()` | `tuple[float, float]` | Current Bezier point at `t`. |
| `sample(n=100)` | `list[dict]` | `n` sampled points along the curve. |
