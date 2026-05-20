# GraphWidget API

::: wigglystuff.graph_widget.GraphWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `nodes` | `list[dict]` | Node dicts with normalized `id` and optional `name`, `size`, `color`, and `data`. |
| `edges` | `list[dict]` | Edge dicts with normalized `id`, `source`, `target`, and optional `name`, `width`, `color`, and `data`. |
| `directed` | `bool` | Draw directed edges when true. |
| `bounded` | `bool` | Keep nodes inside the visible SVG bounds when true. Disable it for graphs that should spread beyond the viewport and be explored with pan/zoom. |
| `width` | `int \| None` | Canvas width in pixels. `None` (default) makes the widget fill its container's width and reflow when the container resizes. |
| `height` | `int` | Canvas height in pixels (default `400`). |
| `selected_nodes` | `list[str]` | IDs of currently selected nodes. |
| `selected_edges` | `list[str]` | IDs of currently selected edges. |

## Layout Notes

`GraphWidget` preserves browser-side node positions when `nodes` or `edges`
change. Newly connected nodes are initialized near the existing endpoint they
attach to. Use `attach_node(source, name, ...)` when adding one new node plus
its connecting edge from Python; if `name` or `id` already resolves to a node,
only the edge is added. Use `detach_node(node)` to remove all edges attached to
a node while keeping the node visible, or `detach_node(node, delete=True)` to
remove the node too.
