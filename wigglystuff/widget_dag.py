"""WidgetDAG -- arrange live widgets as a DAG and draw the arrows for you."""

from __future__ import annotations

from pathlib import Path

import anywidget
import traitlets


class _Arrows(anywidget.AnyWidget):
    """A pure SVG overlay that connects ``[data-wdag-node]`` boxes per ``edges``.

    It owns no content of its own: the ESM climbs out of its shadow root to the
    ``[data-wdag-root]`` container ``WidgetDAG`` laid out and draws arrows into
    it, so the SVG shares a coordinate space with the node boxes.
    """

    _esm = Path(__file__).parent / "static" / "widget-dag.js"
    edges = traitlets.List().tag(sync=True)


def layered_layout(nodes, edges):
    """Assign each node a column (0 = leftmost).

    Longest-path layering, then pull every node rightward to sit just before
    its earliest child. That keeps edges between adjacent columns for
    pipeline/tree shapes, so arcs stay inside the empty column gaps and never
    cross a widget. (True long edges would still skip -- that needs dummy
    waypoint nodes; a job for a future layout strategy.)

    A layout is just ``(nodes, edges) -> {id: column}``; pass your own to
    ``WidgetDAG(..., layout=...)`` to swap in a different algorithm.
    """
    parents = {k: [] for k in nodes}
    children = {k: [] for k in nodes}
    for src, dst in edges:
        parents[dst].append(src)
        children[src].append(dst)
    col = {}

    def longest(k):
        if k not in col:
            col[k] = 0 if not parents[k] else 1 + max(longest(p) for p in parents[k])
        return col[k]

    for k in nodes:
        longest(k)
    changed = True
    while changed:  # pull right: latest column still left of every child
        changed = False
        for k in nodes:
            if children[k]:
                latest = min(col[c] for c in children[k]) - 1
                if latest > col[k]:
                    col[k] = latest
                    changed = True
    return col


class WidgetDAG:
    """Lay widgets out as a DAG and draw the arrows -- like ``mo.hstack``, but
    columns come from edge depth and the connections are drawn for you.

    ``nodes`` maps an id to any renderable (an input widget, an image, a chart
    -- anything marimo can show). ``edges`` is a list of ``(src_id, dst_id)``.
    ``layout`` is ``(nodes, edges) -> {id: column}`` (default ``layered_layout``).
    The widgets stay live and reactive; this only arranges references to them.

    This is a marimo-only display helper: the arrow overlay reaches into
    marimo's rendered DOM, so it is not wired for plain Jupyter.

    Example:
        ```python
        import marimo as mo
        from wigglystuff import Matrix, WidgetDAG

        kernel = mo.ui.anywidget(Matrix(rows=3, cols=3))
        WidgetDAG(
            nodes={"kernel": kernel, "image": mo.image("cat.png"), "conv": out},
            edges=[("image", "conv"), ("kernel", "conv")],
        )
        ```
    """

    def __init__(self, nodes, edges, layout=layered_layout):
        self.nodes = dict(nodes)
        self.edges = [list(e) for e in edges]
        self.layout = layout

    def _display_(self):
        import marimo as mo

        depth = self.layout(self.nodes, self.edges)
        columns = []
        for lvl in range(max(depth.values(), default=0) + 1):
            boxes = [
                mo.md(
                    f'<div data-wdag-node="{k}" style="display:inline-flex;'
                    f'flex-direction:column;align-items:center;gap:4px">{v}'
                    f'<span style="font:11px monospace;color:#888">{k}</span></div>'
                )
                for k, v in self.nodes.items()
                if depth[k] == lvl
            ]
            columns.append(mo.vstack(boxes, gap=1.5, align="center"))
        board = mo.hstack(columns, gap=4, align="center", justify="start")
        overlay = mo.ui.anywidget(_Arrows(edges=self.edges))
        return mo.md(
            f'<div data-wdag-root style="position:relative;'
            f'display:inline-block">{board}{overlay}</div>'
        )
