---
title: "CurveEditor: draggable D3 curve editor"
description: CurveEditor is a chart-space curve editor with draggable knots, switchable D3 interpolators, and sampled path points synced back to Python in marimo or Jupyter.
image: curveeditor
image_alt: CurveEditor widget showing two D3 curves with draggable knots, a curve-type dropdown, and a tension slider
---

# CurveEditor API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="curveeditor" data-demo-title="CurveEditor live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/curveeditor.webp" alt="CurveEditor widget showing two D3 curves with draggable knots, a curve-type dropdown, and a tension slider" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`CurveEditor` is a chart-space curve editor: drag the knots and switch among D3's line
interpolators — `natural`, `catmull_rom`, `step`, `monotone_x` and friends — to see how
each one reads through the same points. Open curves keep their points sorted by x so they
behave like ordinary chart lines, while closed curves preserve drawing order so a loop
stays editable as drawn. `samples` streams points along the rendered path back to Python,
and `playing` sweeps `t` along it.

See also: [BezierCurve](bezier-curve.md) for control-point Bezier curves instead of
interpolated knots, [SplineDraw](spline-draw.md) for fitting a curve to points you paint,
and [Slider2D](slider2d.md) for dragging a single x/y point.

::: wigglystuff.curve_editor.CurveEditor

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `points` | `list[dict]` | Chart knots as `{"x": float, "y": float}` in data coordinates. Open curves store points sorted by x-coordinate; closed curves preserve drawing order. |
| `samples` | `list[dict]` | `n_samples` points along the rendered curve in data coordinates, emitted by the browser after each render. |
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
| `show_axes` | `bool` | Whether to render numeric tick marks and labels on the x and y axes. |
| `n_samples` | `int` | Number of points emitted on the `samples` traitlet. Must be at least 2. |
| `x_bounds` | `tuple[float, float]` | Data-coordinate x bounds. |
| `y_bounds` | `tuple[float, float]` | Data-coordinate y bounds. |
| `width` | `int` | SVG width in pixels. |
| `height` | `int` | SVG height in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `current_point()` | `tuple[float, float]` | Current path progress point. In Python this is a linear knot approximation; the browser syncs from the actual rendered D3 path. |
