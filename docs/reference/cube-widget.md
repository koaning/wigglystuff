---
title: "CubeWidget: 3D plane, line and point picker"
description: CubeWidget renders an isometric cube whose axes lock one by one, so clicking them selects a plane, then a line, then a point synced back to Python.
image: cube-widget
image_alt: CubeWidget showing an isometric cube with a locked red plane, green line and blue point, labelled Angle, Force and Time
---

# CubeWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="cube_widget" data-demo-title="CubeWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/cube-widget.webp" alt="CubeWidget showing an isometric cube with a locked red plane, green line and blue point, labelled Angle, Force and Time" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`CubeWidget` draws three named axes as an isometric cube and locks them one at a time:
the first click picks a plane, the second narrows it to a line, the third to a single
point. Each lock reveals a slider for that axis value, and `plane`, `line` and `point`
sync back to Python so downstream cells can slice a grid of results the same way. Use
`lock_axis()`, `unlock_axis()` and `reset()` to drive the same selection from code.

See also: [ThreeWidget](three-widget.md) for plotting the points themselves in 3D,
[Slider2D](slider2d.md) for steering two continuous parameters at once, and
[Matrix](matrix.md) for editing the grid of numbers a slice comes from.

::: wigglystuff.cube_widget.CubeWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `x_axis` | `dict` | X-axis display name and numeric values. |
| `y_axis` | `dict` | Y-axis display name and numeric values. |
| `z_axis` | `dict` | Z-axis display name and numeric values. |
| `locked_order` | `list[str]` | Axis keys in plane → line → point lock order. |
| `axis_values` | `dict[str, float]` | Current value for each axis key. |
| `plane` | `dict | None` | First locked axis display name and value. |
| `line` | `dict | None` | Second locked axis display name and value. |
| `point` | `dict | None` | Third locked axis display name and value. |

## Helpers

- `lock_axis(axis_key, value=None)` locks an axis and optionally sets its value.
- `unlock_axis(axis_key)` removes an axis from the lock order.
- `reset()` clears every lock while preserving the current axis values.
