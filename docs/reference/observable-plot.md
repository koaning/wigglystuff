---
title: "ObservablePlot: Observable Plot in Python"
description: ObservablePlot runs Observable Plot JavaScript from a string, file or URL in a notebook, injecting pandas or polars data into the chart scope by name.
image: observable-plot
image_alt: ObservablePlot rendering an Observable Plot line chart of intraday price with a smoothed trend line
---

# ObservablePlot API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="observableplot" data-demo-title="ObservablePlot live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/observable-plot.webp" alt="ObservablePlot rendering an Observable Plot line chart of intraday price with a smoothed trend line" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ObservablePlot` is a thin runner for [Observable Plot](https://observablehq.com/plot/): it
loads Plot and d3 from a CDN, evaluates the JavaScript you hand it — inline, from a local
file, or from a URL — and mounts the DOM node that expression returns. Python values passed
in `variables` become in-scope JavaScript variables, with DataFrames and numpy arrays
converted to JSON records first. Reassigning `code` or `variables` rebuilds the chart, and
the new node is swapped in only once it is ready, so slider-driven updates never flash a
blank frame.

See also: [AltairWidget](altair-widget.md) for driving a Vega-Lite spec from Python,
[EsmWidget](esm-widget.md) for running any CDN library with a two-way `data` bridge, and
[RidgelineChart](ridgeline-chart.md) for a chart that needs no JavaScript at all.

::: wigglystuff.observable_plot.ObservablePlot

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved Observable Plot JavaScript (inline JS, or the contents of a file / URL, fetched in Python), evaluated as an expression that returns the DOM node to mount. |
| `variables` | `dict` | Name → value mapping injected into the code's scope as JavaScript variables. DataFrames and numpy arrays are converted to JSON records/lists on assignment. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `version` | `str` | `@observablehq/plot` version loaded from the CDN (defaults to `"latest"`). |
| `error` | `str` | Read-back of the latest JS runtime / CDN-load error, or `""`. |
