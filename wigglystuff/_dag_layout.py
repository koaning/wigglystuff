"""Layout and marimo-graph helpers shared by WidgetFlow, WidgetDAG and FormulaDAG."""

from __future__ import annotations

from html import escape
from itertools import permutations

# Prefix for dummy "waypoint" node ids inserted for edges that span more than
# one layer. It starts with "!" so it can never equal a real node id (those
# are Python identifiers), while staying a valid HTML attribute value.
_WP = "!wdag_wp"
_FLOAT_PRECISION = 4


def _format_float_html(value):
    """Return compact HTML for a bare float, or ``None`` for other nodes."""
    if not isinstance(value, float):
        return None
    exact = repr(value)
    compact = format(value, f".{_FLOAT_PRECISION}g")
    return (
        f'<span title="Exact value: {escape(exact)}">'
        f"{escape(compact)}</span>"
    )


def _require_marimo_notebook(name="WidgetFlow"):
    """Raise unless we are displaying inside a running marimo notebook.

    These helpers render by reaching into marimo's rendered DOM, so they are a
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
        f"{name} is a marimo-only display helper: it renders by reaching "
        "into marimo's rendered DOM and does not work outside a running "
        "marimo notebook."
    )


def _check_acyclic(nodes, edges, describe=str):
    """Raise ``ValueError`` naming the cycle if ``edges`` loop back on themselves.

    ``describe`` turns a node id into the text used in the message.
    """
    children = {k: [] for k in nodes}
    for src, dst in edges:
        children[src].append(dst)
    state = {}  # absent = unvisited, 1 = on the current path, 2 = done
    path = []

    def visit(k):
        state[k] = 1
        path.append(k)
        for c in children[k]:
            if state.get(c) == 1:
                loop = path[path.index(c):] + [c]
                raise ValueError("edges form a cycle: " + " -> ".join(describe(n) for n in loop))
            if c not in state:
                visit(c)
        path.pop()
        state[k] = 2

    for k in nodes:
        if k not in state:
            visit(k)


def layered_layout(nodes, edges):
    """Assign each node a layer (0 = first).

    Longest-path layering, then pull every node forward to sit just before
    its earliest child. That keeps edges between adjacent layers for
    pipeline/tree shapes, so arrows stay inside the empty gaps between layers
    and never cross a widget. Longer edges get routed through waypoint lanes.

    A layout is just ``(nodes, edges) -> {id: layer}``; pass your own to
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
    while changed:  # pull forward: latest layer still before every child
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
    land in the same layer -- correct for independent inputs.
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


def _marimo_context(caller):
    """The running marimo kernel context, or a clear ``RuntimeError``."""
    try:
        from marimo._runtime.context.types import get_context

        return get_context()
    except Exception as e:  # not in a marimo kernel
        raise RuntimeError(
            f"{caller} needs a running marimo kernel; pass the edges "
            "yourself outside marimo."
        ) from e


def _variable_names(objs, glb):
    """``{id(obj): name}`` for each object bound to a top-level variable in
    ``glb`` (first match wins). Objects without a variable are left out."""
    wanted = {id(o) for o in objs}
    names = {}
    for name, val in glb.items():
        if id(val) in wanted and id(val) not in names and not name.startswith("_"):
            names[id(val)] = name
    return names


def _infer_edges(widgets, caller="from_widgets"):
    """Derive ``(src, dst)`` edges between ``widgets`` from marimo's dataflow
    graph. Returns ``(edges, names)``: edges as pairs of the widget objects
    themselves, and ``{id(widget): variable name}``.

    Every widget must be a top-level variable; two widgets defined in the same
    cell get no edge between them (marimo's graph is cell-level).
    """
    ctx = _marimo_context(caller)
    names = _variable_names(widgets, ctx.globals)
    if any(id(w) not in names for w in widgets):
        raise ValueError(
            f"Every widget passed to {caller} must be a top-level variable; "
            "one object was not found in the notebook globals. Assign it to "
            "a variable or pass the edges yourself."
        )
    order = [names[id(w)] for w in widgets]
    obj_of = {names[id(w)]: w for w in widgets}
    name_to_cell = {n: next(iter(ctx.graph.definitions[n])) for n in order}
    ancestors = {c: ctx.graph.ancestors(c) for c in name_to_cell.values()}
    edges = [(obj_of[u], obj_of[v]) for u, v in _reduce_edges(order, name_to_cell, ancestors)]
    return edges, names


def _order_and_route(order, columns, edges, sweeps=8, brute_cap=6, direct=()):
    """Order the nodes within each layer to reduce edge crossings, and split
    every edge that spans more than one layer with dummy waypoint nodes.

    ``order`` seeds each layer (ties broken by input order), ``columns`` maps a
    node to its layer (from the layout), and ``edges`` is ``[[u, v], ...]`` with
    ``columns[u] < columns[v]``. Edges listed in ``direct`` (as ``(u, v)``
    tuples) still count for ordering but get no waypoints: their route is just
    ``[u, v]``, for callers that route those arrows freely. Returns
    ``(layers, routes, dummies)``:

    - ``layers`` -- ``{layer: [id, ...]}`` in order (ids are real node names or
      ``_WP``-prefixed waypoints).
    - ``routes`` -- one chain ``[u, *waypoints, v]`` per edge, so a long edge is
      drawn through the reserved (empty) waypoint lanes instead of over a widget.
    - ``dummies`` -- the set of waypoint ids.

    Ordering is the standard layer-by-layer crossing minimization: split long
    edges into single-layer segments, then repeatedly pick, for each layer, the
    order that minimizes crossings with the neighbouring layer. Graphs that
    admit a crossing-free order under the assigned layering can reach zero; the
    rest are minimized, not guaranteed (that is NP-hard). Layers wider than
    ``brute_cap`` keep their seeded order rather than brute-forcing.
    """
    direct = {tuple(e) for e in direct}
    max_col = max(columns.values(), default=0)
    layers = {c: [] for c in range(max_col + 1)}
    for n in order:
        layers[columns[n]].append(n)

    seg_children = {}  # node -> nodes one layer further on (after splitting)
    routes = []
    dummies = set()
    for u, v in edges:
        if (u, v) in direct:
            seg_children.setdefault(u, []).append(v)
            routes.append([u, v])
            continue
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
