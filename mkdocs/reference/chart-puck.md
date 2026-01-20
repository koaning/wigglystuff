# ChartPuck API

::: wigglystuff.chart_puck.ChartPuck

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
| `puck_color` | `str` | CSS color of puck(s). |
