---
title: "SplineDraw: draw points, fit a spline"
description: SplineDraw pairs a paintable scatter canvas with a spline fitted in Python by your own callback, so the curve updates as you draw points in Jupyter or marimo.
image: splinedraw
image_alt: SplineDraw widget showing two classes of hand-painted scatter points with a fitted spline curve through each
---

# SplineDraw API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="splinedraw" data-demo-title="SplineDraw live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/splinedraw.webp" alt="SplineDraw widget showing two classes of hand-painted scatter points with a fitted spline curve through each" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`SplineDraw` puts a paintable scatter canvas in front of a fit you write yourself: pass a
`spline_fn(x, y) -> (x_curve, y_curve)` callable and the curve is recomputed in Python
every time you draw. Reach for it when you want to show what a smoother, a regression
spline, or any other one-dimensional fit does to data you invent on the spot. With up to
four point classes each class gets its own fitted curve, and `curve_error` surfaces
whatever the callback raised.

See also: [ScatterWidget](scatter-widget.md) for the same drawing canvas without the fit,
[CurveEditor](curve-editor.md) for placing knots by hand instead of fitting them, and
[ChartSelect](chart-select.md) for selecting regions of data you already have.

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
