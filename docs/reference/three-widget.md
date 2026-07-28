---
title: "ThreeWidget: 3D scatter plot in notebooks"
description: ThreeWidget draws a Three.js 3D scatter plot from a list of points with per-point color and size, and can animate updates in marimo or Jupyter.
image: threewidget
image_alt: ThreeWidget showing a rotatable cube of rainbow-colored 3D points
---

# ThreeWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="threewidget" data-demo-title="ThreeWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/threewidget.webp" alt="ThreeWidget showing a rotatable cube of rainbow-colored 3D points" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ThreeWidget` renders a list of `{"x", "y", "z"}` dicts as a Three.js point cloud you
can orbit with the mouse, with optional per-point `color` and `size`. Reach for it when
a 2D scatter hides the structure you care about — embeddings, sensor traces, parameter
sweeps. `update_points()` swaps the data in place and, with `animate_updates=True`,
tweens between frames instead of redrawing from scratch.

See also: [CubeWidget](cube-widget.md) for picking a slice out of a 3D parameter space,
[ParallelCoordinates](parallel-coords.md) for data with more than three dimensions, and
[HoverZoom](hover-zoom.md) for magnifying a crowded 2D plot instead.

::: wigglystuff.three_widget.ThreeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict[str, Any]]` | Point list with `x`, `y`, `z`, and optional `color`/`size`. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `show_grid` | `bool` | Show the grid helper. |
| `show_axes` | `bool` | Show the axes helper. |
| `dark_mode` | `bool` | Toggle dark background and lighting. |
| `axis_labels` | `list[str]` | Optional labels for x/y/z axes. |
| `animate_updates` | `bool` | Animate transitions when updating points. |
| `animation_duration_ms` | `int` | Duration for animated updates in milliseconds. |
