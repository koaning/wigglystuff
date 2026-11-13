"""WidgetFlow -- live widgets as a FormulaDAG-style, top-to-bottom DAG."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping

import anywidget
import traitlets

from .formula_dag import _PRODUCER_COLORS
from .widget_dag import WidgetDAG, _format_float_html, _order_and_route, layered_layout

_CSS_PATH = Path(__file__).parent / "static" / "widget-flow.css"
_INK = {"light": "#8a8378", "dark": "#a39b8f"}
DIRECTIONS = ("down", "right")
NOTE_SIDES = ("auto", "left", "right", "top", "bottom")
PORT_SIDES = ("auto", "top", "bottom", "left", "right")
COLOR_BY = ("source", "none")
_MONO = {"light": "#6f685e", "dark": "#b4ac9f"}


def _port(value, what):
    """Normalise an edge end to ``{"side": ..., "at": float | None}``."""
    if value is None:
        return None
    side, at = (value, None) if isinstance(value, str) else tuple(value)
    if side not in PORT_SIDES:
        raise ValueError(f"{what} side must be one of {PORT_SIDES}, got {side!r}.")
    if at is not None and not 0 <= float(at) <= 1:
        raise ValueError(f"{what} position must be between 0 and 1, got {at!r}.")
    if side == "auto":
        return None
    return {"side": side, "at": None if at is None else float(at)}


class _FlowOverlay(anywidget.AnyWidget):
    """Draws the arrows, notes, groups and toolbar into the ``[data-wf-root]``
    container ``WidgetFlow`` laid out. It owns no content of its own."""

    _esm = Path(__file__).parent / "static" / "widget-flow.js"
    routes = traitlets.List().tag(sync=True)
    edges = traitlets.List().tag(sync=True)
    edge_labels = traitlets.Dict().tag(sync=True)
    ports = traitlets.Dict().tag(sync=True)
    edge_colors = traitlets.Dict().tag(sync=True)
    beside = traitlets.Dict().tag(sync=True)
    colors = traitlets.Dict().tag(sync=True)
    groups = traitlets.List().tag(sync=True)
    direction = traitlets.Unicode("down").tag(sync=True)
    collapsed = traitlets.List().tag(sync=True)
    selected = traitlets.Unicode("").tag(sync=True)
    toolbar = traitlets.Bool(True).tag(sync=True)
    theme = traitlets.Unicode("auto").tag(sync=True)


def _rows(nodes, edges, pins):
    """Longest-path layering, then honour ``rows`` pins (push a node down to at
    least that row; whatever depends on it moves down with it)."""
    depth = layered_layout(nodes, edges)
    parents = {k: [] for k in nodes}
    for src, dst in edges:
        parents[dst].append(src)
    out = {}

    def row(k):
        if k not in out:
            above = [row(p) + 1 for p in parents[k]]
            out[k] = max([depth[k], pins.get(k, 0), *above])
        return out[k]

    for k in nodes:
        row(k)
    return out


class WidgetFlow(WidgetDAG):
    r"""Lay live widgets out as a DAG that reads like ``FormulaDAG``.

    Nodes flow top to bottom (or left to right) and every node that feeds
    another gets its own color, shared by its caption dot and its arrows. Hover
    a caption to light up everything upstream and downstream; click it to pin
    that focus. Each card can be collapsed to its caption, and a small toolbar
    flips the direction and collapses or expands everything.

    By default every node that feeds another gets its own color from the
    ``FormulaDAG`` palette. Pass ``color_by="none"`` for plain, single-color
    arrows, ``colors={"node": "#hex"}`` to pin a node's color, or a ``"color"``
    key in an edge's options to color one arrow.

    ``beside={"noise": ("fit", "left")}`` puts a node on the same row as the
    node it feeds, to its left or right, so its arrow runs straight into that
    side instead of dropping in from above.

    Annotate the graph with ``notes`` (a plain-language note beside a node,
    with an arrow onto it), edge labels (a third item in an edge tuple), and
    ``groups`` (a dashed, labelled region around related nodes).

    An edge's third item can also be a dict that says where the arrow leaves
    its source and lands on its target: ``{"label": "x, y", "exit": "right",
    "enter": ("left", 0.3)}``. A side is ``"top"``, ``"bottom"``, ``"left"``,
    ``"right"`` or ``"auto"``; the optional number places the port along that
    side (0 to 1). The toolbar's ``ports`` mode lets you drag arrow ends onto a
    side instead and shows the matching Python to paste back.

    Like ``WidgetDAG`` this is a marimo-only display helper; the widgets stay
    live and reactive.

    Example:
        ```python
        WidgetFlow(
            nodes={"n": n_slider, "noise": noise, "data": chart, "fit": fit},
            edges=[("n", "data"), ("noise", "data"), ("data", "fit", "train")],
            notes={"noise": "std of the gaussian noise"},
            groups={"inputs": ["n", "noise"]},
        )
        ```
    """

    def __init__(
        self,
        nodes: Mapping[str, Any],
        edges,
        *,
        labels: Mapping[str, str] | None = None,
        notes: Mapping[str, Any] | None = None,
        groups: Mapping[str, Any] | None = None,
        colors: Mapping[str, str] | None = None,
        color_by: str = "source",
        rows: Mapping[str, int] | None = None,
        beside: Mapping[str, Any] | None = None,
        direction: str = "down",
        collapsed=(),
        toolbar: bool = True,
        theme: str = "auto",
        layout=None,
    ) -> None:
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
        if color_by not in COLOR_BY:
            raise ValueError(f"color_by must be one of {COLOR_BY}, got {color_by!r}")
        if theme not in ("auto", "light", "dark"):
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")
        edges = [tuple(e) for e in edges]
        for e in edges:
            if len(e) not in (2, 3):
                raise ValueError("each edge must be (src, dst) or (src, dst, label).")
            for end in e[:2]:
                if end not in nodes:
                    raise ValueError(f"edge {e!r} names unknown node {end!r}.")
        super().__init__(nodes, [e[:2] for e in edges], layout=layout or layered_layout)
        self.edge_labels = {}
        self.ports = {}
        self.edge_colors = {}
        for e in edges:
            if len(e) < 3 or e[2] is None:
                continue
            key = f"{e[0]}->{e[1]}"
            spec = e[2] if isinstance(e[2], Mapping) else {"label": e[2]}
            extra = set(spec) - {"label", "exit", "enter", "color"}
            if extra:
                raise ValueError(f"edge {key} has unknown options {sorted(extra)}.")
            if spec.get("label") is not None:
                self.edge_labels[key] = str(spec["label"])
            if spec.get("color") is not None:
                self.edge_colors[key] = {"light": str(spec["color"]), "dark": str(spec["color"])}
            ends = {k: _port(spec.get(k), f"edge {key} {k}") for k in ("exit", "enter")}
            if any(ends.values()):
                self.ports[key] = ends
        self.labels = dict(labels or {})
        self.notes = {k: v if isinstance(v, Mapping) else {"text": v} for k, v in (notes or {}).items()}
        for k, spec in self.notes.items():
            if k not in self.nodes:
                raise ValueError(f"note for unknown node {k!r}.")
            if spec.get("side", "auto") not in NOTE_SIDES:
                raise ValueError(f"note side must be one of {NOTE_SIDES}.")
        self.groups = {}
        for name, spec in (groups or {}).items():
            spec = dict(spec) if isinstance(spec, Mapping) else {"nodes": list(spec)}
            unknown = [n for n in spec["nodes"] if n not in self.nodes]
            if unknown:
                raise ValueError(f"group {name!r} names unknown nodes {unknown}.")
            self.groups[name] = spec
        self.colors = dict(colors or {})
        self.color_by = color_by
        self.rows = dict(rows or {})
        self.beside = {}
        for k, spec in (beside or {}).items():
            anchor, side = (spec, "right") if isinstance(spec, str) else tuple(spec)
            if k not in self.nodes or anchor not in self.nodes:
                raise ValueError(f"beside {k!r}: {anchor!r} must both be nodes.")
            if side not in ("left", "right"):
                raise ValueError(f"beside {k!r} side must be 'left' or 'right', got {side!r}.")
            if k == anchor:
                raise ValueError(f"beside {k!r} cannot sit next to itself.")
            self.beside[k] = {"anchor": anchor, "side": side}
        for k, spec in self.beside.items():
            if spec["anchor"] in self.beside:
                raise ValueError(f"beside {k!r}: {spec['anchor']!r} is itself placed beside another node.")
        self.direction = direction
        self.collapsed = list(collapsed)
        self.toolbar = toolbar
        self.theme = theme

    @classmethod
    def from_widgets(cls, widgets, **kwargs):
        dag = WidgetDAG.from_widgets(widgets)
        return cls(dag.nodes, dag.edges, **kwargs)

    def _node_colors(self):
        producers = []
        for src, _ in self.edges:
            if src not in producers:
                producers.append(src)
        out = {}
        for i, k in enumerate(producers):
            palette = _PRODUCER_COLORS[i % len(_PRODUCER_COLORS)]
            out[k] = dict(palette if self.color_by == "source" else _MONO)
        for k, css in self.colors.items():
            out[k] = {"light": css, "dark": css}
        return {k: out.get(k, dict(_INK)) for k in self.nodes}

    def _display_(self):
        from .widget_dag import _require_marimo_notebook

        _require_marimo_notebook()
        import marimo as mo

        main = {k: v for k, v in self.nodes.items() if k not in self.beside}
        main_edges = [e for e in self.edges if e[0] in main and e[1] in main]
        if self.layout is layered_layout:
            depth = _rows(main, main_edges, self.rows)
        else:
            depth = self.layout(main, main_edges)
        layers, routes, dummies = _order_and_route(list(main), depth, main_edges)
        routes = routes + [list(e) for e in self.edges if e[0] in self.beside or e[1] in self.beside]
        flank = {}
        for k, spec in self.beside.items():
            flank.setdefault((spec["anchor"], spec["side"]), []).append(k)
        colors = self._node_colors()

        def note_html(k):
            spec = self.notes.get(k)
            if not spec:
                return ""
            text = spec["text"]
            body = mo.md(text) if isinstance(text, str) else mo.as_html(text)
            color = spec.get("color")
            style = f' style="--wf-note-c:{escape(color)}"' if color else ""
            return (
                f'<div class="wf-note" data-wf-note="{escape(k)}" '
                f'data-side="{escape(spec.get("side", "auto"))}"{style}>{body.text}</div>'
            )

        def item_html(k):
            value = self.nodes[k]
            body = _format_float_html(value) or mo.as_html(value).text
            c = colors[k]
            label = escape(self.labels.get(k, k))
            return (
                f'<div class="wf-item" data-wf-item="{escape(k)}">'
                f'<div class="wf-card" data-wf-node="{escape(k)}" '
                f'style="--wf-c-light:{c["light"]};--wf-c-dark:{c["dark"]}">'
                f'<div class="wf-head" data-wf-head="{escape(k)}" title="hover: trace · click: pin">'
                f'<span class="wf-dot"></span><span class="wf-label">{label}</span>'
                f'<button class="wf-fold" data-wf-fold="{escape(k)}" title="collapse">'
                f"</button></div>"
                f'<div class="wf-body">{body}</div></div>{note_html(k)}</div>'
            )

        parts = []
        for lvl in sorted(layers):
            items = []
            for k in layers[lvl]:
                if k in dummies:
                    items.append(f'<div class="wf-lane" data-wf-node="{k}"></div>')
                    continue
                left, right = flank.get((k, "left"), []), flank.get((k, "right"), [])
                if not (left or right):
                    items.append(item_html(k))
                    continue
                row = "".join(item_html(n) for n in [*left, k, *right])
                items.append(f'<div class="wf-cluster">{row}</div>')
            parts.append(f'<div class="wf-layer">{"".join(items)}</div>')

        overlay = mo.ui.anywidget(
            _FlowOverlay(
                routes=routes,
                edges=[list(e) for e in self.edges],
                edge_labels=self.edge_labels,
                ports=self.ports,
                edge_colors=self.edge_colors,
                beside=self.beside,
                colors=colors,
                groups=[{"name": n, **s} for n, s in self.groups.items()],
                direction=self.direction,
                collapsed=self.collapsed,
                toolbar=self.toolbar,
                theme=self.theme,
            )
        )
        return mo.Html(
            f'<div data-wf-root class="wf" data-direction="{self.direction}">'
            f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>"
            f'<div class="wf-board">{"".join(parts)}</div>{overlay.text}</div>'
        )
