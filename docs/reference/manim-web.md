---
title: "ManimWeb: run Manim in the browser"
description: ManimWeb loads the manim-web engine from a CDN and plays a scene you supply as a JS string, local file, or URL, inline in a marimo notebook.
image: manim-web
image_alt: ManimWeb widget showing a shaded teal sphere animated on labelled x, y and z axes
---

# ManimWeb API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="manim_web" data-demo-title="ManimWeb live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/manim-web.webp" alt="ManimWeb widget showing a shaded teal sphere animated on labelled x, y and z axes" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ManimWeb` loads [manim-web](https://github.com/maloyan/manim-web) — a TypeScript/WebGL
reimplementation of Manim that renders in the browser — from a CDN, then runs a scene you
supply as an inline JS string, a path to a local file, or a URL. Your code runs with the
`manim` namespace, the `container` element, the `width`/`height` ints and the widget
`model` in scope; manim-web's own `Player` draws a full playback UI with a scrub timeline,
speed control and export. Python's only job is handing over the source and the sizing.
The code is executed verbatim in the browser, so only pass JavaScript you trust.

See also: [EsmWidget](esm-widget.md) for running any other CDN library the same way,
[ObservablePlot](observable-plot.md) for JS charts fed by Python values, and
[FramePlayer](frame-player.md) for playing back frames you rendered in Python.

::: wigglystuff.manim_web.ManimWeb

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Resolved scene JavaScript (inline JS, or the contents of a file / URL, fetched in Python), run against the manim-web `manim` namespace and a `container` element. |
| `width` | `int` | Container width in pixels. |
| `height` | `int` | Container height in pixels. |
| `version` | `str` | manim-web version loaded from the CDN. |
| `error` | `str` | Read-back of the latest JS runtime error, or `""`. |
