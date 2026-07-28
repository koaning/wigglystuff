---
title: "GridDraw: draw dots and lines on a grid"
description: GridDraw snaps dots to the intersections of a square grid and draws orthogonal segments between them, syncing both back to Python as integer coordinates.
image: griddraw
image_alt: GridDraw showing black dots on grid intersections and horizontal and vertical line segments drawn between them, with a small toolbar above
---

# GridDraw API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="griddraw" data-demo-title="GridDraw live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/griddraw.webp" alt="GridDraw showing black dots on grid intersections and horizontal and vertical line segments drawn between them, with a small toolbar above" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`GridDraw` constrains drawing to a square grid: dots land on intersections and lines are
unit segments between neighboring intersections, always horizontal or vertical. Because
everything is addressed as integer `[row, col]` coordinates from `[0, 0]` to
`[rows, cols]`, `dots` and `lines` come back to Python as lists you can index a maze,
board or layout with instead of pixels you have to interpret. Pass a list to
`line_width` to get a width picker in the toolbar.

See also: [Paint](paint.md) for freehand painting on a canvas, [EdgeDraw](edge-draw.md)
for node and link diagrams, and [Matrix](matrix.md) for typing numbers into a grid
rather than drawing on one.

::: wigglystuff.grid_draw.GridDraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `dots` | `list` | Drawn intersections as `[[row, col], ...]`. |
| `lines` | `list` | Drawn unit segments as `{"from": [r, c], "to": [r, c], "width": int}` dictionaries. |
| `rows` | `int` | Number of grid cells vertically; row intersections are `0..rows`. |
| `cols` | `int` | Number of grid cells horizontally; column intersections are `0..cols`. |
| `line_width` | `int \| list[int]` | Fixed line width, or picker options when a list is supplied. |
| `dot_radius` | `int` | Drawn dot radius in pixels. |
| `theme` | `str \| None` | `None` follows the notebook; `"light"` or `"dark"` forces the widget theme. |
| `width` | `int` | Widget width in pixels. |
| `height` | `int` | Widget height in pixels. |
