---
title: "HoverZoom: image magnifier on hover"
description: HoverZoom pairs an image with a magnified side panel that tracks your cursor, the e-commerce product zoom pattern, for inspecting dense plots in Jupyter.
image: hoverzoom
image_alt: HoverZoom showing a dense labelled scatter plot with a dashed rectangle marking the region being magnified
---

# HoverZoom API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="hoverzoom" data-demo-title="HoverZoom live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/hoverzoom.webp" alt="HoverZoom showing a dense labelled scatter plot with a dashed rectangle marking the region being magnified" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`HoverZoom` shows an image with a rectangle indicator under the cursor and a magnified
panel beside it — the e-commerce product zoom pattern, aimed at plots. It is handy when a
matplotlib figure has more points than pixels and the overlapping labels only separate
under magnification. It takes a figure, file path, URL, PIL image, bytes or base64
string, and `get_pil_zoom()` returns the region currently under the cursor as an image.

See also: [ChartPuck](chart-puck.md) for dragging a control point over a chart,
[WebcamCapture](webcam-capture.md) for getting images into the notebook in the first
place, and [FramePlayer](frame-player.md) for stepping through a sequence of images.

::: wigglystuff.hover_zoom.HoverZoom

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `image` | `str` | Base64-encoded image data. |
| `zoom_factor` | `float` | Magnification level for the zoom panel. |
| `width` | `int` | Display width of the source image in pixels. |
| `height` | `int` | Display height in pixels (0 = auto). |
