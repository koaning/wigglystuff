---
title: "ImageRefreshWidget: update an image in place"
description: ImageRefreshWidget swaps an image source in place so a loop can redraw the same matplotlib plot in a Jupyter cell instead of stacking up new output.
image: imagerefresh
image_alt: ImageRefreshWidget rendering a matplotlib line chart of a cumulative sum below the cell that created it
---

# ImageRefreshWidget API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="htmlwidget" data-demo-title="ImageRefreshWidget live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/imagerefresh.webp" alt="ImageRefreshWidget rendering a matplotlib line chart of a cumulative sum below the cell that created it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ImageRefreshWidget` renders one `<img>` element and repoints it at a new `src` whenever
that traitlet changes, so a running loop can redraw a single image slot rather than emit a
fresh picture per iteration. `src` is normally a base64 data URI; the
`wigglystuff.utils.refresh_matplotlib` decorator turns a plotting function into exactly
that, which is the usual way this widget gets fed.

See also: [HTMLRefreshWidget](html-refresh.md) for the same in-place trick with arbitrary
markup, [ProgressBar](progress-bar.md) for reporting how far the loop has got, and
[FramePlayer](frame-player.md) for replaying frames once the loop has finished.

::: wigglystuff.html.ImageRefreshWidget

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `src` | `str` | The image source, typically a base64-encoded data URI. |
