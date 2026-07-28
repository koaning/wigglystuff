---
title: "EdgeDraw: sketch a graph, get its matrix"
description: EdgeDraw lets you drag links between labeled nodes in a notebook and hands the sketch back to Python as an adjacency matrix, neighbor lists or cycle checks.
image: edgedraw
image_alt: EdgeDraw showing four labeled nodes on a canvas with two arrows drawn between them
---

# EdgeDraw API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="edgedraw" data-demo-title="EdgeDraw live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/edgedraw.webp" alt="EdgeDraw showing four labeled nodes on a canvas with two arrows drawn between them" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`EdgeDraw` starts from a list of node labels and lets you drag from one node to another
to add a link, which arrives in Python on `links` as `{"source": ..., "target": ...}`
dicts. Reach for it when the graph is what you are trying to express rather than
something you already have in data: `get_adjacency_matrix()`, `get_neighbors()` and
`has_cycle()` turn the sketch into something you can compute on.

See also: [GraphWidget](graph-widget.md) for graphs supplied from Python rather than
drawn, [GridDraw](grid-draw.md) for dots and lines snapped to a grid, and
[Excalidraw](excalidraw.md) for freehand diagrams that are not meant to be parsed.

::: wigglystuff.edge_draw.EdgeDraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `names` | `list[str]` | Ordered node labels. |
| `links` | `list[dict]` | Link dicts with `source` and `target` keys. |
| `directed` | `bool` | Draw directed edges when true. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |

