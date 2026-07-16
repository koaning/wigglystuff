# WidgetDAG API

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
