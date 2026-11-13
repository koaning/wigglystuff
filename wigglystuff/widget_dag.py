"""WidgetDAG -- arrange live widgets as a DAG and draw the arrows for you."""

from __future__ import annotations

import warnings
from pathlib import Path

import anywidget
import traitlets

from ._dag_layout import (  # noqa: F401  (re-exported for back-compat)
    _WP,
    _format_float_html,
    _infer_edges,
    _order_and_route,
    _reduce_edges,
    _require_marimo_notebook,
    layered_layout,
)


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


class WidgetDAG:
    """Lay widgets out as a DAG and draw the arrows -- like ``mo.hstack``, but
    columns come from edge depth and the connections are drawn for you.

    .. deprecated::
        ``WidgetDAG`` is deprecated in favour of ``WidgetFlow``, which draws
        FormulaDAG-style arrows and adds notes, edge labels, ports, captions and
        a ``direction`` switch. ``WidgetDAG.from_widgets([...])`` becomes
        ``WidgetFlow.from_widgets([...], direction="right")``; for
        ``WidgetDAG(nodes, edges)`` pass the widget objects as a list and the
        edges as pairs of objects. Constructing a ``WidgetDAG`` emits a
        ``FutureWarning``.

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
        warnings.warn(
            "WidgetDAG is deprecated; use WidgetFlow instead "
            "(WidgetFlow.from_widgets for edges inferred from marimo).",
            FutureWarning,
            stacklevel=2,
        )
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
        edges, names = _infer_edges(widgets, caller="WidgetDAG.from_widgets")
        nodes = {names[id(w)]: w for w in widgets}
        edges = [[names[id(u)], names[id(v)]] for u, v in edges]
        return cls(nodes, edges, layout=layout)

    def _repr_mimebundle_(self, **kwargs):
        # marimo prefers ``_display_``, so this only fires in Jupyter/IPython,
        # where it turns a silent plain-text repr into a clear error.
        _require_marimo_notebook("WidgetDAG")

    def _display_(self):
        _require_marimo_notebook("WidgetDAG")
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
                    node_html = _format_float_html(self.nodes[k])
                    if node_html is None:
                        node_html = mo.as_html(self.nodes[k])
                    boxes.append(
                        mo.md(
                            f'<div data-wdag-node="{k}" style="display:inline-flex;'
                            f'flex-direction:column;align-items:center;gap:4px">'
                            f"{node_html}"
                            f'<span style="font:11px monospace;color:#888">{k}</span></div>'
                        )
                    )
            columns.append(mo.vstack(boxes, gap=1.5, align="center"))
        # gap=6 reserves a clear inter-column corridor for tight turns and heads.
        board = mo.hstack(columns, gap=6, align="center", justify="start")
        overlay = mo.ui.anywidget(_Arrows(routes=routes))
        return mo.md(
            f'<div data-wdag-root style="position:relative;'
            f'display:inline-block">{board}{overlay}</div>'
        )
