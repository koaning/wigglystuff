---
title: "BezierCurve: draggable Bezier curve editor"
description: BezierCurve is an arbitrary-degree Bezier editor with draggable control points, playback along the curve, and sampled points synced back to Python.
image: beziercurve
image_alt: BezierCurve widget showing a Bezier curve with draggable control points
---

# BezierCurve API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="beziercurve" data-demo-title="BezierCurve live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/beziercurve.webp" alt="BezierCurve widget showing a Bezier curve with draggable control points" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`BezierCurve` is an arbitrary-degree Bezier editor: drag the control points and the
curve follows, while `samples` streams evenly spaced points along it back to Python.
Set `playing` to sweep the parameter `t` from 0 to 1 and animate anything downstream
of `x`/`y`.

See also: [CurveEditor](curve-editor.md) for D3 line interpolators in chart space,
[SplineDraw](spline-draw.md) for fitting a spline to drawn points, and
[Slider2D](slider2d.md) for a single draggable x/y point.

::: wigglystuff.bezier_curve.BezierCurve

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `points` | `list[dict]` | Control points as `{"x": float, "y": float}` in data coordinates. |
| `samples` | `list[dict]` | `n_samples` points along the rendered curve in data coordinates. |
| `x` | `float` | Current Bezier point x-coordinate at `t`. |
| `y` | `float` | Current Bezier point y-coordinate at `t`. |
| `t` | `float` | Curve parameter, clamped to `[0, 1]`. |
| `closed` | `bool` | Whether to virtually append the first point so the curve returns to the start. |
| `playing` | `bool` | Whether playback is currently advancing `t`. |
| `loop` | `bool` | Whether playback wraps from `t=1` to `t=0`. |
| `interval_ms` | `int` | Milliseconds between browser playback ticks. |
| `duration_ms` | `int` | Milliseconds for one full `t=0` to `t=1` traversal. |
| `sync_throttle_ms` | `int` | Minimum milliseconds between playback updates synced to Python. |
| `show_axes` | `bool` | Whether to render numeric tick marks and labels on the x and y axes. |
| `n_samples` | `int` | Number of points emitted on the `samples` traitlet. Must be at least 2. |
| `x_bounds` | `tuple[float, float]` | Data-coordinate x bounds. |
| `y_bounds` | `tuple[float, float]` | Data-coordinate y bounds. |
| `width` | `int` | SVG width in pixels. |
| `height` | `int` | SVG height in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `current_point()` | `tuple[float, float]` | Current Bezier point at `t`. |
| `sample(n=100)` | `list[dict]` | `n` sampled points along the curve. |
