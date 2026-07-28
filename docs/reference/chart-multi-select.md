---
title: "ChartMultiSelect: label chart regions"
description: ChartMultiSelect keeps several class-labeled box or lasso regions on a matplotlib chart so you can hand-label scatter points in marimo or Colab notebooks.
image: chartmultiselect
image_alt: ChartMultiSelect widget showing blue and orange lasso regions labeling the two moons of a matplotlib scatter plot
---

# ChartMultiSelect API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="chartmultiselect" data-demo-title="ChartMultiSelect live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/chartmultiselect.webp" alt="ChartMultiSelect widget showing blue and orange lasso regions labeling the two moons of a matplotlib scatter plot" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ChartMultiSelect` is `ChartSelect` with memory: every box or lasso you draw over the
matplotlib PNG stays on the canvas tagged with a class label, up to four classes. Draw one
region per class and `get_labels(x, y)` returns a class per point, with `-1` for anything
unclassified and last-drawn winning where regions overlap. It is a quick way to hand-label
a scatter plot before training on it.

See also: [ChartSelect](chart-select.md) for a single throwaway selection,
[ScatterWidget](scatter-widget.md) for painting labeled points instead of labeling
existing ones, and [ChartPuck](chart-puck.md) for dragging a point on the same kind of
chart overlay.

::: wigglystuff.chart_multi_select.ChartMultiSelect

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `mode` | `str` | Selection mode: "box" or "lasso". |
| `modes` | `list[str]` | Available modes (controls which buttons are shown). |
| `n_classes` | `int` | Number of class labels (1–4). |
| `active_class` | `int` | Currently active class for the next drawn selection. |
| `selections` | `list[dict]` | All selections. Each dict has `type`, `class_id`, and geometry keys. |
| `selected_index` | `int` | Index of the highlighted selection (-1 = none). |
| `x_bounds` | `tuple[float, float]` | Min/max x-axis bounds from matplotlib. |
| `y_bounds` | `tuple[float, float]` | Min/max y-axis bounds from matplotlib. |
| `axes_pixel_bounds` | `tuple[float, float, float, float]` | Axes position in pixels (left, top, right, bottom). |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `chart_base64` | `str` | Base64-encoded PNG of the matplotlib figure. |
| `selection_opacity` | `float` | Opacity of selection fill (0-1). |
| `stroke_width` | `int` | Width of selection border in pixels. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `clear()` | `None` | Remove all selections. |
| `get_labels(x_arr, y_arr)` | `ndarray[int]` | Class labels per point (-1 = unclassified, last-drawn wins for overlap). |
| `get_mask(x_arr, y_arr, class_id=None)` | `ndarray[bool]` | Boolean mask for classified points (optionally filtered by class). |
| `get_indices(x_arr, y_arr, class_id=None)` | `ndarray[int]` | Indices of classified points. |
| `redraw()` | `None` | Re-render chart (only for `from_callback` widgets). |
