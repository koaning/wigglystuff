---
title: "ParallelCoordinates: HiPlot in a notebook"
description: ParallelCoordinates wraps HiPlot so you can brush axes, drag them into a new order and read the filtered rows back as a DataFrame inside Jupyter.
image: parallelcoords
image_alt: ParallelCoordinates showing colored polylines across labeled axes with two brush selections active
---

# ParallelCoordinates API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="parallelcoords" data-demo-title="ParallelCoordinates live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/parallelcoords.webp" alt="ParallelCoordinates showing colored polylines across labeled axes with two brush selections active" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ParallelCoordinates` wraps [HiPlot](https://github.com/facebookresearch/hiplot) so every row
of your data becomes one polyline across a set of draggable axes, colored by whichever column
you pass to `color_by`. Brush an axis to select rows, then keep or exclude them — from the
buttons or from `keep()` / `exclude()` in Python — and pull the survivors back out through
`filtered_data`, `filtered_as_pandas` or `filtered_as_polars`. Reach for it when you are
sifting a hyperparameter sweep or any table with more numeric columns than a scatter plot
can hold.

See also: [RidgelineChart](ridgeline-chart.md) for many same-shaped series stacked as
waveforms, [ChartSelect](chart-select.md) for box and lasso selection on a matplotlib
figure, and [NestedTable](nested-table.md) for reading the numbers instead of the lines.

::: wigglystuff.parallel_coords.ParallelCoordinates

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list[dict]` | Input rows rendered as polylines. |
| `color_by` | `str` | Column used for line coloring. |
| `color_map` | `dict` | Map of categorical values to CSS colors (e.g. `{"a": "red", "b": "#00f"}`). Unmapped values use the default palette. |
| `height` | `int` | Plot height in pixels. |
| `width` | `int` | Plot width in pixels. Set to 0 for container width. |
| `brush_extents` | `dict` | Current brush ranges on axes. Resets to `{}` after Keep/Exclude. |
| `filtered_indices` | `list[int]` | Indices currently passing filters/selection. |
| `selected_indices` | `list[int]` | Indices currently selected in the active brush. |

## Methods

| Method | Description |
| --- | --- |
| `selections` | Property returning `filter_history` + a trailing `{"action": "current", "extents": ...}` entry for the active brush (if any). |
| `keep()` | Trigger a Keep action on the current brush selection (same as the Keep button). |
| `exclude()` | Trigger an Exclude action on the current brush selection (same as the Exclude button). |
| `restore()` | Restore all rows and clear `filter_history` (same as the Restore button). |
| `filtered_data` | Property returning the list of dicts for rows passing all filters. |
| `filtered_as_pandas` | Property returning filtered data as a pandas DataFrame. |
| `filtered_as_polars` | Property returning filtered data as a polars DataFrame. |
| `selected_data` | Property returning the list of dicts for selected rows. |
