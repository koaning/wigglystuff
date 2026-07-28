---
title: "Excalidraw: whiteboard in your notebook"
description: Excalidraw embeds the Excalidraw whiteboard in a Jupyter or Colab notebook, keeping the scene in Python and handing the finished drawing back as a PIL image.
image: excalidraw
image_alt: Excalidraw whiteboard showing a hand-drawn box and circle joined by an arrow, with the shape and freehand tool palette above
---

# Excalidraw API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="excalidraw" data-demo-title="Excalidraw live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/excalidraw.webp" alt="Excalidraw whiteboard showing a hand-drawn box and circle joined by an arrow, with the shape and freehand tool palette above" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`Excalidraw` puts the Excalidraw whiteboard in a notebook cell: an infinite canvas with
shapes, arrows, text and freehand strokes. Excalidraw and React are fetched from a CDN
the first time the widget renders, so it needs network access. The drawing lives on the
`scene` traitlet and nothing is written to disk until you call `save()`; `get_pil()`
hands the board to Python as an image — handy for a multimodal model — and
`Excalidraw.from_file()` loads a saved `.excalidraw` file back.

See also: [Paint](paint.md) for a smaller MS-Paint-style canvas, [GridDraw](grid-draw.md)
for dots and lines snapped to a grid, and [EdgeDraw](edge-draw.md) for node and link
diagrams you can compute on.

::: wigglystuff.excalidraw.Excalidraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `scene` | `dict` | Excalidraw scene (`elements` / `appState` / `files`). |
| `image_base64` | `str` | PNG data URL of the drawing; read via `get_pil()`. |
| `theme` | `str` | `"light"` (default) or `"dark"`; `""` follows the notebook theme. |
| `height` | `int` | Canvas height in pixels. |
| `sync_throttle_ms` | `int` | Minimum delay between syncing edits back to Python. |

Excalidraw itself is loaded from a CDN the first time the widget renders, so the
widget needs network access and does not work fully offline.
