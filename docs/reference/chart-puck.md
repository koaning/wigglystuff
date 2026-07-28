---
title: "ChartPuck: drag a puck on a matplotlib plot"
description: ChartPuck overlays a draggable puck on a static matplotlib figure and reports its position in data coordinates, turning a plot into an input control in marimo.
image: chartpuck
image_alt: ChartPuck widget showing a green puck dragged over a matplotlib scatter plot with crosshair guides and its coordinates in the title
---

# ChartPuck API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="chartpuck" data-demo-title="ChartPuck live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/chartpuck.webp" alt="ChartPuck widget showing a green puck dragged over a matplotlib scatter plot with crosshair guides and its coordinates in the title" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ChartPuck` renders your matplotlib figure once to a base64 PNG and floats a draggable
puck on top of it, so the chart stays a static image and only the puck moves. `x` and `y`
report the puck position in the axes' own data coordinates, which makes an existing plot
usable as an input control. Pass lists to get several pucks at once, `throttle` to choose
between syncing every drag move and syncing on release, and `from_callback` when the
figure itself should be redrawn as the puck moves.

See also: [Slider2D](slider2d.md) for a bare x/y pad with no chart behind it,
[ChartSelect](chart-select.md) for selecting a region of the same chart instead of a
point, and [ChartMultiSelect](chart-multi-select.md) for labeling several regions.

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
| `puck_color` | `str \| list[str]` | CSS color(s) of puck(s). A single color applies to all; a list assigns one per puck. |
| `throttle` | `int \| str` | Drag sync rate. `0` = every move, int = ms throttle, `"dragend"` = on release. |
