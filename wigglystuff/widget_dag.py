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


def _require_marimo_notebook():
    """Raise unless we are displaying inside a running marimo notebook.

    ``WidgetDAG`` renders by reaching into marimo's rendered DOM, so it is a
    no-op anywhere else. Mirrors the ``mo.running_in_notebook()`` check in
    ``wigglystuff/_marimo_notice.py``.
    """
    try:
        import marimo as mo

        if mo.running_in_notebook():
            return
    except ImportError:
        pass
    raise RuntimeError(
        "WidgetDAG is a marimo-only display helper: it renders by reaching "
        "into marimo's rendered DOM and does not work outside a running "
        "marimo notebook."
    )


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


def _reduce_edges(order, name_to_cell, ancestors):
    """Derive DAG edges between nodes from their cells' ancestry.

    ``order`` is the list of node names (input order), ``name_to_cell`` maps each
    name to its defining cell id, and ``ancestors`` maps a cell id to the set of
    its transitive ancestor cell ids. Returns ``[[u, v], ...]``.

    An edge ``u -> v`` exists when ``u``'s cell is an ancestor of ``v``'s cell,
    then transitively reduced: ``u -> v`` is dropped if some other node ``w``
    sits on the path (``u`` ancestor of ``w`` and ``w`` ancestor of ``v``). Nodes
    that share a cell are neither each other's ancestor, so they get no edge and
    land in the same column -- correct for independent inputs.
    """

    def is_anc(a, b):  # cell(a) is an ancestor of cell(b)
        return name_to_cell[a] in ancestors.get(name_to_cell[b], set())

    edges = []
    for v in order:
        for u in order:
            if u == v or not is_anc(u, v):
                continue
            if any(w not in (u, v) and is_anc(u, w) and is_anc(w, v) for w in order):
                continue
            edges.append([u, v])
    return edges


class WidgetDAG:
    """Lay widgets out as a DAG and draw the arrows -- like ``mo.hstack``, but
    columns come from edge depth and the connections are drawn for you.

    ``nodes`` maps an id to any renderable (an input widget, an image, a chart
    -- anything marimo can show). ``edges`` is a list of ``(src_id, dst_id)``.
    ``layout`` is ``(nodes, edges) -> {id: column}`` (default ``layered_layout``).
    The widgets stay live and reactive; this only arranges references to them.

    This is a marimo-only display helper: the arrow overlay reaches into
    marimo's rendered DOM, so it is not wired for plain Jupyter.

    Instead of spelling out ``edges`` by hand, ``WidgetDAG.from_widgets`` derives
    them from marimo's own dataflow graph -- pass the widgets and the arrows
    follow the notebook's dependency order (see that method).

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

    @classmethod
    def from_widgets(cls, widgets, *, layout=layered_layout):
        """Build a ``WidgetDAG`` from a list of widgets, deriving the arrows from
        marimo's dataflow graph.

        Pass the widget objects (not their names); each node is labelled with the
        Python variable it is bound to, and an edge is drawn between two widgets
        whenever the cell defining one depends on the cell defining the other.

        ```python
        WidgetDAG.from_widgets([paint, angle, kernel, conv, kernel2, conv2])
        ```

        This only works when each widget is a top-level variable defined in its
        own cell -- marimo's graph is cell-level, so two variables computed in the
        same cell can't be ordered, and inline expressions aren't variables at
        all. For those cases use ``WidgetDAG(nodes, edges)`` directly. Requires a
        running marimo kernel.
        """
        try:
            from marimo._runtime.context.types import get_context

            ctx = get_context()
            graph = ctx.graph
            glb = ctx.globals
        except Exception as e:  # not in a marimo kernel
            raise RuntimeError(
                "WidgetDAG.from_widgets needs a running marimo kernel; "
                "use WidgetDAG(nodes, edges) directly outside marimo."
            ) from e

        # object identity -> variable name (first match wins), preserving order
        name_of = {}
        for w in widgets:
            hit = next((n for n, val in glb.items() if val is w), None)
            if hit is None:
                raise ValueError(
                    "Every widget passed to from_widgets must be a top-level "
                    "variable; one object was not found in the notebook globals. "
                    "Assign it to a variable or use WidgetDAG(nodes, edges)."
                )
            name_of[id(w)] = hit

        order = [name_of[id(w)] for w in widgets]
        nodes = {name_of[id(w)]: w for w in widgets}
        name_to_cell = {n: next(iter(graph.definitions[n])) for n in order}
        ancestors = {c: graph.ancestors(c) for c in name_to_cell.values()}
        edges = _reduce_edges(order, name_to_cell, ancestors)
        return cls(nodes, edges, layout=layout)

    def _repr_mimebundle_(self, **kwargs):
        # marimo prefers ``_display_``, so this only fires in Jupyter/IPython,
        # where it turns a silent plain-text repr into a clear error.
        _require_marimo_notebook()

    def _display_(self):
        _require_marimo_notebook()
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
