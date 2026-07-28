---
title: "RidgelineChart: joy plot ridgeline chart"
description: RidgelineChart stacks the rows of a DataFrame into overlapping waveforms, the Joy Division ridgeline look, and syncs the row you click back to Python.
image: ridgelinechart
image_alt: RidgelineChart showing stacked overlapping pulsar waveforms with one row highlighted in bold
---

# RidgelineChart API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="ridgelinechart" data-demo-title="RidgelineChart live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/ridgelinechart.webp" alt="RidgelineChart showing stacked overlapping pulsar waveforms with one row highlighted in bold" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`RidgelineChart` draws each row of a pandas or polars DataFrame as its own line and lets the
rows overlap, the layout made famous by the PSR B1919+21 pulsar plot on Joy Division's
"Unknown Pleasures". It is a good fit for many same-shaped series — spectra, per-day
distributions, sensor channels — where you care about how the peaks shift from row to row.
Tune `overlap`, `peak_scale` and `fill_opacity` to trade legibility against density, and
read `selected_index` and `selected_row` to find out which waveform was clicked.

See also: [ParallelCoordinates](parallel-coords.md) for comparing many numeric columns of
the same row, [ObservablePlot](observable-plot.md) for writing a chart directly in
JavaScript, and [AltairWidget](altair-widget.md) for a full Vega-Lite spec.

::: wigglystuff.ridgeline_chart.RidgelineChart

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `data` | `list` | Internal data representation: list of {index, values} dicts. |
| `x_values` | `list` | X-coordinates (column names from DataFrame). |
| `width` | `int` | Chart width in pixels. |
| `height` | `int` | Chart height in pixels. |
| `overlap` | `float` | Amount of vertical overlap between rows (0.0 to 1.0). |
| `stroke_width` | `float` | Line stroke width in pixels. |
| `fill_opacity` | `float` | Opacity of the fill beneath each line (0.0 to 1.0). |
| `peak_scale` | `float` | Multiplier for peak height. |
| `x_label` | `str` | Label for the x-axis. |
| `y_label` | `str` | Label for the y-axis. |
| `selected_index` | `Any` | The index of the currently selected row (synced back to Python). |
| `selected_row` | `list` | The values of the currently selected row (synced back to Python). |
