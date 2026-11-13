"""WidgetFlow -- live widgets laid out as a DAG, FormulaDAG style."""

from __future__ import annotations

from html import escape
from pathlib import Path

import anywidget
import traitlets

from ._dag_layout import (
    _check_acyclic,
    _format_float_html,
    _infer_edges,
    _order_and_route,
    _require_marimo_notebook,
    _variable_names,
    layered_layout,
)

_CSS_PATH = Path(__file__).parent / "static" / "widget-flow.css"
DIRECTIONS = ("down", "right")
PORT_SIDES = ("top", "bottom", "left", "right")
EDGE_KEYS = ("label", "exit", "enter", "color", "dashed")
# Where an arrow leaves its source and lands on its target when nothing says
# otherwise: along the flow, out the far side and in at the near side.
_DEFAULT_SIDES = {"down": ("bottom", "top"), "right": ("right", "left")}
# Which way each layer's widgets may be pushed, in screen terms per direction.
ALIGNS = {"down": ("left", "center", "right"), "right": ("top", "center", "bottom")}
# A ``beside`` widget sits after its anchor across the flow: (the widget's side
# that faces the anchor, the anchor's side that faces the widget). One placed
# "before" its anchor swaps the two.
_FACING = {"down": ("left", "right"), "right": ("top", "bottom")}


class _FlowOverlay(anywidget.AnyWidget):
    """Draws the arrows, edge labels and note arrows into the ``[data-wf-root]``
    container ``WidgetFlow`` laid out. It owns no content of its own."""

    _esm = Path(__file__).parent / "static" / "widget-flow.js"
    routes = traitlets.List().tag(sync=True)
    edge_labels = traitlets.Dict().tag(sync=True)
    edge_styles = traitlets.Dict().tag(sync=True)
    ports = traitlets.Dict().tag(sync=True)
    direction = traitlets.Unicode("down").tag(sync=True)
    theme = traitlets.Unicode("auto").tag(sync=True)


def _port(value, what):
    """Normalise one end of a port spec to ``{"side": ..., "at": float | None}``."""
    side, at = (value, None) if isinstance(value, str) else tuple(value)
    if side not in PORT_SIDES:
        raise ValueError(f"{what} side must be one of {PORT_SIDES}, got {side!r}.")
    if at is not None and not 0 <= float(at) <= 1:
        raise ValueError(f"{what} position must be between 0 and 1, got {at!r}.")
    return {"side": side, "at": None if at is None else float(at)}


def _layers_with_pins(nodes, edges, pins):
    """Longest-path layering, then honour ``layers`` pins: push a node down to
    at least its pinned layer; whatever depends on it moves down with it."""
    depth = layered_layout(nodes, edges)
    parents = {k: [] for k in nodes}
    for src, dst in edges:
        parents[dst].append(src)
    out = {}

    def layer(k):
        if k not in out:
            below = [layer(p) + 1 for p in parents[k]]
            out[k] = max([depth[k], pins.get(k, 0), *below])
        return out[k]

    for k in nodes:
        layer(k)
    return out


class WidgetFlow:
    r"""Lay live widgets out as a DAG, in the style of ``FormulaDAG``.

    Pass the widgets (or any renderable: charts, images, ``mo.stat``, ...) as a
    list, and the arrows between them as pairs of those same objects. The
    widgets stay live and reactive; this only arranges references to them. To
    skip the edge list, ``WidgetFlow.from_widgets`` reads the arrows off
    marimo's own dataflow graph.

    This is a marimo-only display helper: the arrow overlay reaches into
    marimo's rendered DOM, so it does not work in plain Jupyter.

    Args:
        nodes: The widgets, in reading order. Each object may appear once.
        edges: ``(src, dst)``, ``(src, dst, "label")`` or ``(src, dst, opts)``
            tuples of the widget objects. ``opts`` is a dict with any of
            ``label`` (plain text beside the arrow), ``exit``/``enter`` (where
            the arrow leaves its source and lands on its target: ``"top"``,
            ``"bottom"``, ``"left"`` or ``"right"``, or a ``(side, position)``
            pair with a position between 0 and 1), ``color`` (any CSS color)
            and ``dashed`` (``True`` for a dashed line).
        direction: ``"down"`` (layers top to bottom) or ``"right"`` (layers
            left to right).
        notes: ``(widget, note)`` pairs. The note (a ``str`` renders as
            markdown, so LaTeX works; any other object renders as-is) sits
            beside the widget with a short arrow onto it.
        ports: ``(src, dst, opts)`` triples that apply ``opts`` (the same dict
            as above) to an arrow that is drawn anyway -- the way to label,
            colour or re-port an edge you didn't spell out, e.g. one
            ``from_widgets`` inferred.
        labels: Captions under the widgets. ``True`` captions each widget with
            the variable it is bound to (needs a marimo kernel),
            ``(widget, "text")`` pairs pick the captions yourself, ``False``
            (default) shows none.
        layers: ``(widget, n)`` pairs push a widget down to at least layer
            ``n`` (0 is the first); whatever depends on it moves with it.
        beside: ``(widget, anchor)`` pairs put ``widget`` in ``anchor``'s
            layer, right after it across the flow (to its right going down,
            below it going right). A third item ``"before"`` puts it right
            before the anchor instead (to its left going down, above it going
            right); ``"after"`` is the default. An arrow between the two
            connects their facing sides unless its ``exit``/``enter`` say
            otherwise. Several widgets on one side of an anchor follow in the
            order given.
        align: where each layer's widgets sit. ``"center"`` (default) centres
            every layer on its own. ``"left"`` or ``"right"`` going down
            (``"top"`` or ``"bottom"`` going right) put all layers on one grid
            packed to that side: the first widget of every layer shares a
            column (the last one, packing right), centred in it, so a chain of
            widgets down that column gets straight arrows.
        theme: ``"auto"`` (follow the notebook), ``"light"`` or ``"dark"``.

    Widgets are referred to by the objects themselves, so options that name a
    widget take ``(widget, value)`` pairs rather than dicts: charts and marimo
    UI elements can't be dict keys.

    The look is tweakable from CSS: ``--wf-edge``, ``--wf-note``, ``--wf-ink``,
    ``--wf-layer-gap`` and ``--wf-node-gap`` on the ``.wf`` root.

    Example:
        ```python
        WidgetFlow(
            [n_points, noise, data_chart, degree, fit_chart],
            edges=[
                (n_points, data_chart),
                (noise, data_chart, "σ"),
                (data_chart, fit_chart, {"label": "x, y", "color": "#c2410c"}),
                (degree, fit_chart, {"enter": "right"}),
            ],
            notes=[(noise, "std of the gaussian noise")],
        )
        ```

        Left-align the layers and put ``degree`` right of the chart it feeds:

        ```python
        WidgetFlow.from_widgets(
            [n_points, noise, data_chart, degree, fit_chart],
            align="left",
            beside=[(degree, fit_chart)],
        )
        ```
    """

    def __init__(
        self,
        nodes,
        edges,
        *,
        direction="down",
        notes=None,
        ports=None,
        labels=False,
        layers=None,
        beside=None,
        align="center",
        theme="auto",
    ):
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}.")
        if align not in ALIGNS[direction]:
            raise ValueError(
                f"with direction={direction!r}, align must be one of "
                f"{ALIGNS[direction]}, got {align!r}."
            )
        if theme not in ("auto", "light", "dark"):
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")
        self.nodes = list(nodes)
        self.direction = direction
        self.align = align
        self.theme = theme
        self._key = {}
        for i, obj in enumerate(self.nodes):
            if id(obj) in self._key:
                raise ValueError(f"nodes[{i}] appears more than once in nodes.")
            self._key[id(obj)] = f"n{i}"

        # edges and their options, keyed "nA->nB"
        self._edges = []
        opts = {}
        for e in edges:
            if len(e) not in (2, 3):
                raise ValueError("each edge must be (src, dst) or (src, dst, label_or_opts).")
            s, d = self._key_of(e[0], "edge"), self._key_of(e[1], "edge")
            if (s, d) in self._edges:
                raise ValueError(f"edge {self._name(s, d)} is given more than once.")
            self._edges.append((s, d))
            if len(e) == 3 and e[2] is not None:
                opts[f"{s}->{d}"] = self._edge_opts(e[2], self._name(s, d))
        _check_acyclic(
            list(self._key.values()), self._edges, describe=lambda k: f"nodes[{k[1:]}]"
        )

        # beside: {widget key: anchor key}, in the order given, and the
        # widgets that go before their anchor rather than after it
        self.beside = {}
        self._before = set()
        for entry in beside or []:
            if len(entry) not in (2, 3):
                raise ValueError(
                    "each beside entry must be a (widget, anchor) pair or a "
                    '(widget, anchor, "before"/"after") triple.'
                )
            w, a = self._key_of(entry[0], "beside"), self._key_of(entry[1], "beside")
            side = entry[2] if len(entry) == 3 else "after"
            if side not in ("before", "after"):
                raise ValueError(f'beside side must be "before" or "after", got {side!r}.')
            if w == a:
                raise ValueError(f"nodes[{w[1:]}] can't be placed beside itself.")
            if w in self.beside:
                raise ValueError(f"nodes[{w[1:]}] appears in beside more than once.")
            self.beside[w] = a
            if side == "before":
                self._before.add(w)
        for w, a in self.beside.items():
            if a in self.beside:
                raise ValueError(
                    f"nodes[{a[1:]}] is an anchor in beside but is itself placed "
                    "beside another widget; anchor every widget on one that isn't."
                )
        # a beside widget shares its anchor's layer, so for layering the two
        # are one node; a path anchor -> ... -> widget makes that impossible
        try:
            _check_acyclic(
                [k for k in self._key.values() if k not in self.beside],
                self._layer_edges(),
                describe=lambda k: f"nodes[{k[1:]}]",
            )
        except ValueError:
            raise ValueError(
                "beside puts a widget in its anchor's layer, but the edges connect "
                "the two through other widgets, so one must sit above the other."
            ) from None

        for p in ports or []:
            if len(p) != 3:
                raise ValueError("each port must be a (src, dst, opts) triple.")
            s, d = self._key_of(p[0], "port"), self._key_of(p[1], "port")
            if (s, d) not in self._edges:
                raise ValueError(f"port given for an arrow that isn't drawn ({self._name(s, d)}).")
            opts.setdefault(f"{s}->{d}", {}).update(self._edge_opts(p[2], self._name(s, d)))
        self.edges = [(self.nodes[int(s[1:])], self.nodes[int(d[1:])]) for s, d in self._edges]

        self.edge_labels, self.edge_styles, self.ports = {}, {}, {}
        default_exit, default_enter = _DEFAULT_SIDES[direction]
        for key, o in opts.items():
            if o.get("label") is not None:
                self.edge_labels[key] = str(o["label"])
            style = {k: o[k] for k in ("color", "dashed") if o.get(k)}
            if style:
                self.edge_styles[key] = style
            ends = {k: o[k] for k in ("exit", "enter") if k in o}
            # an end on its default side with no position is no port at all:
            # the arrow is drawn like any other
            if ends.get("exit") == {"side": default_exit, "at": None}:
                del ends["exit"]
            if ends.get("enter") == {"side": default_enter, "at": None}:
                del ends["enter"]
            if ends:
                self.ports[key] = ends
        # an arrow between a beside widget and its anchor runs within one
        # layer, so it always takes the freely routed path, between the
        # sides that face each other unless its opts named others
        for s, d in self._edges:
            if self.beside.get(s) == d:
                w, sides = s, _FACING[direction]
            elif self.beside.get(d) == s:
                w, sides = d, _FACING[direction][::-1]
            else:
                continue
            if w in self._before:
                sides = sides[::-1]
            key = f"{s}->{d}"
            given = {k: v for k, v in opts.get(key, {}).items() if k in ("exit", "enter")}
            self.ports[key] = {
                "exit": given.get("exit", {"side": sides[0], "at": None}),
                "enter": given.get("enter", {"side": sides[1], "at": None}),
            }

        self.notes = {}
        for obj, text in notes or []:
            k = self._key_of(obj, "note")
            if k in self.notes:
                raise ValueError(f"nodes[{k[1:]}] has more than one note.")
            self.notes[k] = text

        if labels is True:
            names = self._globals_names()
            self.labels = {self._key[i]: n for i, n in names.items()}
        elif labels is False or labels is None:
            self.labels = {}
        else:
            self.labels = {self._key_of(o, "label"): str(t) for o, t in labels}

        self.layers = {}
        for obj, n in layers or []:
            if not isinstance(n, int) or n < 0:
                raise ValueError(f"layers values must be non-negative ints, got {n!r}.")
            k = self._key_of(obj, "layers")
            if k in self.beside:
                raise ValueError(
                    f"nodes[{k[1:]}] is placed beside another widget, so it takes "
                    "that widget's layer; pin the anchor in layers instead."
                )
            self.layers[k] = n

    def _layer_edges(self):
        """The edges with each beside widget merged into its anchor (and the
        arrows between the two dropped), for layering."""
        out = []
        for s, d in self._edges:
            s, d = self.beside.get(s, s), self.beside.get(d, d)
            if s != d:
                out.append((s, d))
        return out

    @classmethod
    def from_widgets(cls, widgets, *, labels=True, **kwargs):
        """Build a ``WidgetFlow`` whose arrows come from marimo's dataflow graph.

        One widget points at another when the cell defining the second depends
        on the cell defining the first (transitively reduced, so a chain
        ``a -> b -> c`` gets no shortcut ``a -> c``). Each widget is captioned
        with its variable name unless you pass ``labels=False`` or a dict.
        Every other keyword is passed to ``WidgetFlow``.

        ```python
        WidgetFlow.from_widgets([paint, angle, kernel, conv], direction="right")
        ```

        This needs each widget to be a top-level variable in its own cell:
        marimo's graph is cell-level, so two variables computed in one cell
        can't be ordered, and inline expressions aren't variables at all. For
        those, pass ``edges`` to ``WidgetFlow`` yourself. Requires a running
        marimo kernel.
        """
        edges, names = _infer_edges(list(widgets), caller="WidgetFlow.from_widgets")
        if labels is True:
            labels = [(w, names[id(w)]) for w in widgets]
        return cls(widgets, edges, labels=labels, **kwargs)

    def upstream(self, widget):
        """Every node that feeds ``widget``, directly or not, in node order."""
        return self._lineage(widget, up=True)

    def downstream(self, widget):
        """Every node ``widget`` feeds, directly or not, in node order."""
        return self._lineage(widget, up=False)

    def _lineage(self, widget, up):
        start = self._key_of(widget)
        step = {}
        for s, d in self._edges:
            a, b = (d, s) if up else (s, d)
            step.setdefault(a, []).append(b)
        seen, todo = set(), [start]
        while todo:
            for nxt in step.get(todo.pop(), []):
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return [o for o in self.nodes if self._key[id(o)] in seen]

    def _key_of(self, obj, what="node"):
        """The internal id of a node object (raises if it isn't one)."""
        try:
            return self._key[id(obj)]
        except KeyError:
            raise ValueError(f"{what} refers to an object that is not in nodes.") from None

    @staticmethod
    def _name(s, d):
        return f"nodes[{s[1:]}] -> nodes[{d[1:]}]"

    @staticmethod
    def _edge_opts(spec, name):
        """Validate one edge's options: a label string or an opts dict."""
        if isinstance(spec, str):
            return {"label": spec}
        if not isinstance(spec, dict):
            raise ValueError(f"edge {name} options must be a label string or a dict.")
        extra = set(spec) - set(EDGE_KEYS)
        if extra:
            raise ValueError(f"edge {name} has unknown options {sorted(extra)}; use {EDGE_KEYS}.")
        out = dict(spec)
        for k in ("exit", "enter"):
            if spec.get(k) is not None:
                out[k] = _port(spec[k], f"edge {name} {k}")
            else:
                out.pop(k, None)
        return out

    def _globals_names(self):
        """``{id(obj): variable name}`` from the marimo kernel, if there is one."""
        try:
            from marimo._runtime.context.types import get_context

            glb = get_context().globals
        except Exception:
            return {}
        return _variable_names(self.nodes, glb)

    def _repr_mimebundle_(self, **kwargs):
        # marimo prefers ``_display_``, so this only fires in Jupyter/IPython,
        # where it turns a silent plain-text repr into a clear error.
        _require_marimo_notebook("WidgetFlow")

    def _display_(self):
        _require_marimo_notebook("WidgetFlow")
        import marimo as mo

        keys = [self._key[id(o)] for o in self.nodes]
        # layer everything but the beside widgets, which take their anchor's
        depth = _layers_with_pins(
            [k for k in keys if k not in self.beside], self._layer_edges(), self.layers
        )
        for w, a in self.beside.items():
            depth[w] = depth[a]
        # ported arrows route freely around the widgets, so they need no lanes
        ported = [tuple(k.split("->")) for k in self.ports]
        layers, routes, dummies = _order_and_route(
            keys, depth, [list(e) for e in self._edges], direct=ported
        )
        # move each beside widget next to its anchor: just before it, or just
        # after the ones already placed after it, so several on one side keep
        # the order they were given in
        last = {}
        for w, a in self.beside.items():
            row = layers[depth[a]]
            row.remove(w)
            if w in self._before:
                row.insert(row.index(a), w)
            else:
                row.insert(row.index(last.get(a, a)) + 1, w)
                last[a] = w
        objs = dict(zip(keys, self.nodes))

        def item_html(k):
            body = _format_float_html(objs[k]) or mo.as_html(objs[k]).text
            caption = ""
            if k in self.labels:
                caption = f'<div class="wf-caption">{escape(self.labels[k])}</div>'
            note = ""
            if k in self.notes:
                text = self.notes[k]
                html = mo.md(text) if isinstance(text, str) else mo.as_html(text)
                note = f'<div class="wf-note" data-wf-note="{k}">{html.text}</div>'
            return (
                f'<div class="wf-item">'
                f'<div class="wf-node" data-wf-node="{k}">'
                f'<div class="wf-body">{body}</div>{caption}</div>{note}</div>'
            )

        # off-centre alignment lays every layer on one shared grid. A beside
        # widget doesn't take a grid cell of its own there (that would park it
        # past the widest widget of the previous column): it shares its
        # anchor's cell, before or after it, with the anchor kept on the centre
        # line
        grid = self.align != "center"
        cells = {}
        for lvl in sorted(layers):
            cells[lvl] = []
            for k in layers[lvl]:
                if grid and k in self.beside:
                    continue
                html = f'<div class="wf-lane" data-wf-node="{k}"></div>' if k in dummies else item_html(k)
                mine = [w for w in layers[lvl] if self.beside.get(w) == k] if grid else []
                before = "".join(item_html(w) for w in mine if w in self._before)
                after = "".join(item_html(w) for w in mine if w not in self._before)
                if mine:
                    html = (
                        f'<div class="wf-group"><div class="wf-beside wf-before">{before}</div>'
                        f'{html}<div class="wf-beside">{after}</div></div>'
                    )
                cells[lvl].append(html)

        # the k-th cell of each layer sits in column k (counted from the far
        # end for "right"/"bottom"), so widgets stacked in a column share a
        # centre line
        n_cols = max((len(row) for row in cells.values()), default=1)
        span = "grid-row" if self.direction == "right" else "grid-column"
        rows = []
        for lvl in sorted(cells):
            items = cells[lvl]
            skip = n_cols - len(items)
            if self.align in ("right", "bottom") and skip:
                items.insert(0, f'<div style="{span}: span {skip}"></div>')
            rows.append(f'<div class="wf-layer">{"".join(items)}</div>')

        overlay = mo.ui.anywidget(
            _FlowOverlay(
                routes=routes,
                edge_labels=self.edge_labels,
                edge_styles=self.edge_styles,
                ports=self.ports,
                direction=self.direction,
                theme=self.theme,
            )
        )
        css = _CSS_PATH.read_text(encoding="utf-8")
        return mo.Html(
            f'<div data-wf-root class="wf" data-direction="{self.direction}" '
            f'data-align="{self.align}" style="--wf-cols: {n_cols}">'
            f"<style>{css}</style>"
            f'<div class="wf-board">{"".join(rows)}</div>{overlay.text}</div>'
        )
