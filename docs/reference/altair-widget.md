---
title: "AltairWidget: flicker-free Altair charts"
description: AltairWidget renders an Altair chart in a notebook and updates it in place through the Vega View API, so redraws stay smooth instead of flickering.
image: altairwidget
image_alt: AltairWidget showing an Altair line chart rendered in a notebook
---

# AltairWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<div class="wiggly-demo wiggly-demo--static">
<img class="wiggly-demo__poster" src="../assets/gallery/altairwidget.webp" alt="AltairWidget showing an Altair line chart rendered in a notebook" decoding="async">
</div>
</div>
<!-- /no-md -->

`AltairWidget` swaps a chart's data through the Vega View API instead of re-rendering
the whole spec, so driving an Altair chart from a slider updates smoothly rather than
flickering on every change.

Altair is a heavier dependency than the rest of wigglystuff, so this widget has no
in-browser demo — [run it on molab](https://molab.marimo.io/github/koaning/wigglystuff/blob/main/demos/altairwidget.py?utm_source=wigglystuff)
instead. See also: [ObservablePlot](observable-plot.md) for Observable Plot JS,
[ScatterLog](scatter-log.md) for accumulating reactive values into a live scatter, and
[RidgelineChart](ridgeline-chart.md) for stacked waveforms.

::: wigglystuff.altair_widget.AltairWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `spec` | `dict` | Full Vega-Lite spec (from `chart.to_dict()`). |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
