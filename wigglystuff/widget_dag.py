"""WidgetDAG -- arrange live widgets as a DAG and draw the arrows for you."""

from __future__ import annotations

from itertools import permutations
from pathlib import Path

import anywidget
import traitlets

# Prefix for dummy "waypoint" node ids inserted for edges that span more than
# one column. It starts with "!" so it can never equal a real node id (those
# are Python identifiers), while staying a valid HTML attribute value.
_WP = "!wdag_wp"


class _Arrows(anywidget.AnyWidget):
    """A pure SVG overlay that connects ``[data-wdag-node]`` boxes per ``routes``.

    It owns no content of its own: the ESM climbs out of its shadow root to the
    ``[data-wdag-root]`` container ``WidgetDAG`` laid out and draws arrows into
    it, so the SVG shares a coordinate space with the node boxes. Each entry in
    ``routes`` is a chain ``[src, *waypoints, dst]`` of node ids; a long edge is
    routed through the invisible waypoint boxes so it never crosses a widget.
    """

    _esm = Path(__file__).parent / "static" / "widget-dag.js"
    routes = traitlets.List().tag(sync=True)


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


def _order_and_route(order, columns, edges, sweeps=8, brute_cap=6):
    """Order the nodes within each column to reduce edge crossings, and split
    every edge that spans more than one column with dummy waypoint nodes.

    ``order`` seeds each column (ties broken by input order), ``columns`` maps a
    node to its column (from the layout), and ``edges`` is ``[[u, v], ...]`` with
    ``columns[u] < columns[v]``. Returns ``(layers, routes, dummies)``:

    - ``layers`` -- ``{column: [id, ...]}`` in top-to-bottom order (ids are real
      node names or ``_WP``-prefixed waypoints).
    - ``routes`` -- one chain ``[u, *waypoints, v]`` per edge, so a long edge is
      drawn through the reserved (empty) waypoint lanes instead of over a widget.
    - ``dummies`` -- the set of waypoint ids.

    Ordering is the standard layer-by-layer crossing minimization: split long
    edges into single-column segments, then repeatedly pick, for each column, the
    within-column order that minimizes crossings with the neighbouring column. A
    DAG that admits a crossing-free layered drawing (any planar one) reaches
    zero; the rest are minimized, not guaranteed (that is NP-hard). Columns wider
    than ``brute_cap`` keep their seeded order rather than brute-forcing.
    """
    max_col = max(columns.values(), default=0)
    layers = {c: [] for c in range(max_col + 1)}
    for n in order:
        layers[columns[n]].append(n)

    seg_children = {}  # node -> nodes one column to its right (after splitting)
    routes = []
    dummies = set()
    for u, v in edges:
        prev, chain = u, [u]
        for c in range(columns[u] + 1, columns[v]):
            d = f"{_WP}{len(dummies)}"
            dummies.add(d)
            layers[c].append(d)
            seg_children.setdefault(prev, []).append(d)
            prev, _ = d, chain.append(d)
        seg_children.setdefault(prev, []).append(v)
        chain.append(v)
        routes.append(chain)

    def crossings(upper, lower):
        pos_l = {n: i for i, n in enumerate(lower)}
        seg = [
            (i, pos_l[c])
            for i, n in enumerate(upper)
            for c in seg_children.get(n, [])
            if c in pos_l
        ]
        return sum(
            1
            for a in range(len(seg))
            for b in range(a + 1, len(seg))
            if (seg[a][0] - seg[b][0]) * (seg[a][1] - seg[b][1]) < 0
        )

    def best(layer, score):
        return min((list(p) for p in permutations(layer)), key=score)

    for _ in range(sweeps):
        for c in range(1, max_col + 1):
            if len(layers[c]) <= brute_cap:
                layers[c] = best(layers[c], lambda p, c=c: crossings(layers[c - 1], p))
        for c in range(max_col - 1, -1, -1):
            if len(layers[c]) <= brute_cap:
                layers[c] = best(layers[c], lambda p, c=c: crossings(p, layers[c + 1]))
    return layers, routes, dummies


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
        layers, routes, dummies = _order_and_route(list(self.nodes), depth, self.edges)
        columns = []
        for lvl in sorted(layers):
            boxes = []
            for k in layers[lvl]:
                if k in dummies:
                    # an invisible routing lane reserved for a long edge
                    boxes.append(mo.md(f'<div data-wdag-node="{k}" style="height:18px"></div>'))
                else:
                    boxes.append(
                        mo.md(
                            f'<div data-wdag-node="{k}" style="display:inline-flex;'
                            f'flex-direction:column;align-items:center;gap:4px">'
                            f'{mo.as_html(self.nodes[k])}'
                            f'<span style="font:11px monospace;color:#888">{k}</span></div>'
                        )
                    )
            columns.append(mo.vstack(boxes, gap=1.5, align="center"))
        # gap=6 gives edges horizontal room to arrive gently (the overlay keeps
        # them x-monotonic, so more room = flatter approach, never a crossing)
        board = mo.hstack(columns, gap=6, align="center", justify="start")
        overlay = mo.ui.anywidget(_Arrows(routes=routes))
        return mo.md(
            f'<div data-wdag-root style="position:relative;'
            f'display:inline-block">{board}{overlay}</div>'
        )
