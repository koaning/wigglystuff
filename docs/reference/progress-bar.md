---
title: "ProgressBar: progress bar, no ipywidgets"
description: ProgressBar shows loop progress that updates in real time from Python without an ipywidgets dependency, so the same code works in Jupyter, marimo and Colab.
image: progressbar
image_alt: ProgressBar widget showing a filled bar at 100 percent with a 100 slash 100 readout above it
---

# ProgressBar API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="progressbar" data-demo-title="ProgressBar live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/progressbar.webp" alt="ProgressBar widget showing a filled bar at 100 percent with a 100 slash 100 readout above it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ProgressBar` draws a bar that fills as `value` climbs towards `max_value`, with a
`color`, `width`, `height` and an optional `value / max` readout underneath. The reason it
exists is that it does not depend on ipywidgets, so a loop that assigns `bar.value` reports
progress the same way in whatever notebook you happen to be running, and it follows the
surrounding light or dark theme.

See also: [HTMLRefreshWidget](html-refresh.md) for status text updated in place next to it,
[AnnotationWidget](annotation.md) for the labeling queue that bar is often counting, and
[PlaySlider](play-slider.md) when the value should be driven by the reader instead.

::: wigglystuff.html.ProgressBar

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | The current progress value. Defaults to 0. |
| `max_value` | `int` | The maximum value representing 100% completion. Defaults to 100. |
