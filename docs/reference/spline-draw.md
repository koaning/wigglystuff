# SplineDraw API

::: wigglystuff.spline_draw.SplineDraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list` | Drawn scatter points (list of dicts with `x`, `y`, `color`). |
| `curve` | `list` | Fitted curve data computed by the spline function. |
| `curve_error` | `str` | Error message from the last spline computation, or empty string on success. |
| `brushsize` | `int` | Brush radius in pixels. |
| `n_classes` | `int` | Number of point classes (1–4). |
| `width` | `int` | SVG viewBox width in pixels. |
| `height` | `int` | SVG viewBox height in pixels. |
