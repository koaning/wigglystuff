---
title: "Paint: MS-Paint drawing canvas widget"
description: Paint gives a notebook an MS-Paint-style canvas with brush, marker, eraser and color picker, handing what you draw back to Python as a PIL image.
image: paint
image_alt: Paint widget showing a drawing canvas with a brush toolbar
---

# Paint API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="paint" data-demo-title="Paint live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/paint.webp" alt="Paint widget showing a drawing canvas with a brush toolbar" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`Paint` drops an MS-Paint-style canvas into a notebook — brush, marker, eraser,
rainbow spray and a color picker, each toggleable — and hands the result back to
Python as a PIL image via `get_pil()`, ready to feed a model or a preprocessing
pipeline.

See also: [Excalidraw](excalidraw.md) for a full whiteboard, [GridDraw](grid-draw.md)
for snapping dots and lines to a grid, and [ScatterWidget](scatter-widget.md) for
painting labeled 2D datasets.

::: wigglystuff.paint.Paint

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `base64` | `str` | PNG data URL or raw base64 payload. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `store_background` | `bool` | Persist strokes when background changes. |
| `rainbow_brush` | `bool` | Show the rainbow spray tool (default off). |
| `brush` | `bool` | Show the thin brush tool. |
| `marker` | `bool` | Show the thick marker tool. |
| `eraser` | `bool` | Show the eraser tool. |
| `color_picker` | `bool` | Show the color picker. |
| `color` | `str` | Drawing color (hex); two-way synced with the picker. |

