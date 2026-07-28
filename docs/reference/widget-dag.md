---
title: "WidgetDAG: arrange marimo widgets as a DAG"
description: WidgetDAG arranges live marimo widgets, charts and images into columns by edge depth and draws the arrows between them, so a notebook reads as a pipeline.
image: widget-dag
image_alt: WidgetDAG laying out a paint canvas, a slider and two matrices in columns with arrows pointing to the convolved output images
---

# WidgetDAG API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="widget_dag" data-demo-title="WidgetDAG live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/widget-dag.webp" alt="WidgetDAG laying out a paint canvas, a slider and two matrices in columns with arrows pointing to the convolved output images" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`WidgetDAG` is a marimo display helper rather than an AnyWidget: it takes a mapping of
ids to renderables plus a list of `(src, dst)` edges, puts each node in a column
derived from its edge depth, and draws the connecting arrows. Think `mo.hstack`, except
the columns and the arrows come from the graph. The nodes stay live — a `Matrix` or
`Paint` embedded as a node is still editable — and `WidgetDAG.from_widgets([...])` lets
you skip the edge list entirely by reading marimo's own dataflow graph, one node per
cell.

See also: [GraphWidget](graph-widget.md) for a force-directed graph of data instead of
widgets, [EdgeDraw](edge-draw.md) for drawing a graph by hand, and
[ModuleTreeWidget](module-tree.md) for walking a PyTorch module hierarchy.

::: wigglystuff.widget_dag.WidgetDAG

## Layout

A layout is any callable `(nodes, edges) -> {id: column}`. The default is
`layered_layout`; pass your own to `WidgetDAG(..., layout=...)` to swap in a
different algorithm.

::: wigglystuff.widget_dag.layered_layout

## Notes

`WidgetDAG` is a marimo-only display helper. Its arrow overlay reaches into
marimo's rendered DOM to draw connections in the same coordinate space as the
node boxes, so it is not wired for plain Jupyter. The nodes stay live and
reactive — embedding a widget (e.g. a `Matrix` or `Paint`) as a node keeps it
interactive, and editing it re-runs the cell that built the DAG.
