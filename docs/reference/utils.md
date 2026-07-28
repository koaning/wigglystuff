---
title: "wigglystuff utils: charts and refresh helpers"
description: Helper functions in wigglystuff — forecast_chart for exponential time-series projection, altair2svg, and decorators that refresh matplotlib and Altair output in place.
image: forecast-chart
image_alt: Forecast chart showing a time series with a dashed exponential projection
---

# Utils API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="forecast_chart" data-demo-title="ForecastChart live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/forecast-chart.webp" alt="Forecast chart showing a time series with a dashed exponential projection" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

Besides the widgets, `wigglystuff` ships a handful of plain helper functions: one that
builds a forecast chart from a time series, one that converts an Altair chart to SVG,
and two decorators that let a function's plot be swapped in place instead of
re-rendered.

See also: [AltairWidget](altair-widget.md) for flicker-free Altair updates,
[ImageRefreshWidget](image-refresh.md) and [HTMLRefreshWidget](html-refresh.md) for the
widgets the refresh decorators return.

## `forecast_chart`

::: wigglystuff.utils.forecast_chart

---

## `altair2svg` 

::: wigglystuff.utils.altair2svg

---

## `refresh_matplotlib`

::: wigglystuff.utils.refresh_matplotlib

---

## `refresh_altair`

::: wigglystuff.utils.refresh_altair
