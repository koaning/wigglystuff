---
title: "ScatterLog: log points to a live scatter"
description: ScatterLog accumulates points across marimo cell re-runs and appends them to a live Vega-Lite scatter in place, so a growing history survives reactive updates.
image: scatter-log
image_alt: ScatterLog widget showing a trail of points accumulated from dragging a 2D slider, plotted as a live scatter below it
---

# ScatterLog API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="scatter_log" data-demo-title="ScatterLog live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/scatter-log.webp" alt="ScatterLog widget showing a trail of points accumulated from dragging a 2D slider, plotted as a live scatter below it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ScatterLog` accumulates `(x, y[, color])` points and draws them as a live scatter. Where a
plain marimo state variable gets reset by reactivity, a `ScatterLog` instance is stable
across cell re-runs, so it can grow a history: create it once in a dependency-free cell,
then call `.append(...)` from a reactive cell to record a metric, a swept parameter, or
several named series against the same x. It subclasses `AltairWidget`, so each append
patches the Vega view in place — no flicker, and zoom and pan are preserved.

See also: [AltairWidget](altair-widget.md) for the flicker-free chart it builds on,
[ScatterWidget](scatter-widget.md) for drawn points instead of logged ones, and
[ParallelCoordinates](parallel-coords.md) for watching many dimensions at once.

::: wigglystuff.scatter_log.ScatterLog

## Usage

Create the widget once, display it, then append points from a separate reactive
cell. Pass `y=` for one series or use named keyword arguments to append several
series at the same x-coordinate.

```python
log = ScatterLog(x_label="step", y_label="score")
log.append(x=step, loss=loss, accuracy=accuracy)
```

`data` returns a copy of the accumulated points, `clear()` resets the plot, and
`max_points` bounds the retained history.

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `spec` | `dict` | Current Vega-Lite scatter specification. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
