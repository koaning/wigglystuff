---
title: "EsmWidget: run inline JS in a notebook"
description: EsmWidget loads an inline ES module from any CDN and keeps a JSON data value synced both ways, so updates animate instead of redrawing, in Jupyter or marimo.
image: esm-widget
image_alt: EsmWidget widget showing a slider animating a rounded square, above the inline ES module source
---

# EsmWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="esm_widget" data-demo-title="EsmWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/esm-widget.webp" alt="EsmWidget widget showing a slider animating a rounded square, above the inline ES module source" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`EsmWidget` is the escape hatch. You hand it a JavaScript ES module that
`export default { render }`, and it loads that module in the browser and calls `render`.
Because it is loaded as a real module, top-level `import` works, so any CDN library —
motion.dev, Observable Plot, d3, three.js — is one line away. The reason to use it is the
`data` traitlet: a JSON-able value synced both directions where a change fires
`change:data` in the browser without re-running `render`, so your module can tween toward
the new state instead of hard-cutting. Reach for it when nothing packaged fits and the
alternative is writing a whole anywidget from scratch.

See also: [ObservablePlot](observable-plot.md) for Observable Plot with the plumbing
already written, [ManimWeb](manim-web.md) for browser-side Manim scenes, and
[AltairWidget](altair-widget.md) for charts driven from Python instead of JS.

::: wigglystuff.esm_widget.EsmWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved ES module JavaScript (inline JS, or the contents of a file / URL, fetched in Python). Must `export default { render }`; loaded in the browser as a real module, so top-level `import` statements work. |
| `css` | `str` | Optional inline CSS injected into the widget root. |
| `data` | `Any` | Any JSON-able value, synced two-way. Changing it fires `change:data` in the browser but does **not** re-run `render`. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `error` | `str` | Read-back of the latest JS runtime error, or `""`. |
