"""FormulaDAG -- a DAG of LaTeX formulas, wired by where each output is used."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import anywidget
import traitlets

from .tangle_latex import (
    _DEFAULT_COLORS,
    _normalize_notes,
    _normalize_parameters,
)
from .widget_dag import _order_and_route, layered_layout

_ESM_PATH = Path(__file__).parent / "static" / "formula-dag.js"
_CSS_PATH = Path(__file__).parent / "static" / "formula-dag.css"
_USE_RE = re.compile(r"\\use\{([^}]*)\}")
_TANGLE_RE = re.compile(r"\\tangle\{([A-Za-z][A-Za-z0-9_-]*)\}")
_NOTE_RE = re.compile(r"\\note\{([A-Za-z][A-Za-z0-9_-]*)\}")
_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

# In a DAG, color means "this came from formula X", so only producers get a
# palette color: TangleLatex's five, plus three more so mid-sized DAGs don't
# repeat. Numbers and notes default to neutral ink (pass ``color`` to opt in).
_PRODUCER_COLORS = (
    *_DEFAULT_COLORS,
    {"light": "#8a6d00", "dark": "#e3c35a"},
    {"light": "#2f7d32", "dark": "#86d38a"},
    {"light": "#b3262e", "dark": "#ff8a8f"},
)
_PARAM_COLOR = {"light": "#25221d", "dark": "#f2eee8"}
_NOTE_COLOR = {"light": "#6b6459", "dark": "#b8b0a4"}


def _split_lhs(tex: str) -> tuple[str, str] | None:
    """Split ``tex`` at its first top-level ``=`` into ``(lhs, rest)``.

    "Top-level" means outside any ``{...}`` group, so the ``=`` in
    ``\\sum_{i=1}`` is skipped. Returns ``None`` when there is no such ``=`` or
    the part before it is blank.
    """
    depth = 0
    for i, ch in enumerate(tex):
        if ch == "{" and tex[i - 1 : i] != "\\":
            depth += 1
        elif ch == "}" and tex[i - 1 : i] != "\\":
            depth -= 1
        elif ch == "=" and depth == 0:
            lhs = tex[:i].strip()
            return (lhs, tex[i + 1 :]) if lhs else None
    return None


def _strip_notes(tex: str) -> str:
    """Unwrap every ``\\note{name}{body}`` in ``tex`` to just ``body``.

    The default ``\\use`` symbol is a copy of the left-hand side; a note on the
    output (``\\note{why}{d_1} = ...``) explains the formula it sits in and
    must not be copied into every formula that uses it.
    """
    while True:
        m = _NOTE_RE.search(tex)
        if not m or tex[m.end() : m.end() + 1] != "{":
            return tex
        depth, i = 0, m.end()
        for i in range(m.end(), len(tex)):
            if tex[i] == "{" and tex[i - 1] != "\\":
                depth += 1
            elif tex[i] == "}" and tex[i - 1] != "\\":
                depth -= 1
                if depth == 0:
                    break
        tex = tex[: m.start()] + tex[m.end() + 1 : i] + tex[i + 1 :]


def _find_cycle(names: list[str], edges: list[list[str]]) -> list[str] | None:
    """Return one cycle as a list of names (first == last), or ``None``."""
    children = {n: [] for n in names}
    for src, dst in edges:
        children[src].append(dst)
    state = {}  # name -> "visiting" | "done"
    stack = []

    def visit(n):
        state[n] = "visiting"
        stack.append(n)
        for c in children[n]:
            if state.get(c) == "visiting":
                return stack[stack.index(c) :] + [c]
            if c not in state:
                found = visit(c)
                if found:
                    return found
        stack.pop()
        state[n] = "done"
        return None

    for n in names:
        if n not in state:
            found = visit(n)
            if found:
                return found
    return None


def _normalize_formulas(formulas: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Validate the user's ``formulas`` mapping into ``[{name, tex, symbol, label}]``."""
    if not isinstance(formulas, Mapping) or not formulas:
        raise ValueError("formulas must be a non-empty mapping of names to LaTeX.")
    out = []
    for name, raw in formulas.items():
        if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
            raise ValueError(
                f"formula name {name!r} must start with a letter and contain only "
                "letters, numbers, or underscores."
            )
        if isinstance(raw, str):
            raw = {"tex": raw}
        if not isinstance(raw, Mapping):
            raise ValueError(f"formula {name!r} must be a LaTeX string or a mapping.")
        tex = raw.get("tex")
        if not isinstance(tex, str) or not tex.strip():
            raise ValueError(f"formula {name!r} needs a non-empty 'tex' string.")
        split = _split_lhs(tex)
        symbol = raw.get("symbol")
        if symbol is None:
            symbol = _strip_notes(split[0]) if split else rf"\mathrm{{{name}}}"
        label = raw.get("label", name)
        for field, value in (("symbol", symbol), ("label", label)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"formula {name!r} {field} must be a non-empty string.")
        out.append({"name": name, "tex": tex, "symbol": symbol, "label": label})
    return out


def _tangle_and_notes(specs, parameters, notes):
    """Validate the shared ``parameters`` and ``notes`` against the formulas.

    Reuses TangleLatex's normalization, then swaps its palette defaults for
    neutral ink (see ``_PRODUCER_COLORS``). Each note must be marked in
    exactly one formula.
    """
    all_tex = "\n".join(s["tex"] for s in specs)
    params = _normalize_parameters(parameters or {})
    for order, name in enumerate(params):
        if (parameters or {})[name].get("color") is None:
            params[name]["color"] = dict(_PARAM_COLOR)
        # Keep the caller's order for the legend (synced dicts may be re-sorted).
        params[name]["order"] = order

    markers = set(_TANGLE_RE.findall(all_tex))
    missing = sorted(markers - set(params))
    unused = sorted(set(params) - markers)
    if missing:
        raise ValueError("missing configuration for parameter marker(s): " + ", ".join(missing))
    if unused:
        raise ValueError("parameter configuration not referenced by any formula: " + ", ".join(unused))

    normalized_notes = _normalize_notes(notes or {}, latex=all_tex, parameters=params)
    for name, note in normalized_notes.items():
        raw = (notes or {})[name]
        has_color = isinstance(raw, Mapping) and raw.get("color") is not None
        if not has_color and note["param"] is None:
            note["color"] = dict(_NOTE_COLOR)
        homes = [s["name"] for s in specs if name in _NOTE_RE.findall(s["tex"])]
        if len(homes) > 1:
            raise ValueError(
                f"note {name!r} is marked in more than one formula: " + ", ".join(homes)
            )
        note["formula"] = homes[0] if homes else None

    note_markers = set(_NOTE_RE.findall(all_tex))
    missing_notes = sorted(note_markers - set(normalized_notes))
    unused_notes = sorted(set(normalized_notes) - note_markers)
    if missing_notes:
        raise ValueError("missing note for marker(s): " + ", ".join(missing_notes))
    if unused_notes:
        raise ValueError("note(s) not referenced by any formula: " + ", ".join(unused_notes))
    return params, normalized_notes


class FormulaDAG(anywidget.AnyWidget):
    r"""Lay out LaTeX formulas as a DAG, wired by where each output is used.

    Each formula has a name. Writing ``\use{name}`` inside another formula
    renders that formula's output symbol (by default the left-hand side of its
    first ``=``) and draws an arrow from the producing formula straight onto
    the spot where it is used. The edges are inferred from those markers, so
    there is no edge list to maintain; cycles are rejected.

    Formulas flow top to bottom: a formula sits one row below the deepest
    formula it uses. Each producer gets a color shared by its output symbol,
    its arrows, and every place it is used. Hover a formula to highlight what
    it depends on and what depends on it; click it to set ``selected``.

    Numbers and notes work like ``TangleLatex``, shared across the whole DAG:
    ``\tangle{name}`` in any formula is a draggable number configured in
    ``parameters`` (the same name in two formulas is one value), and
    ``\note{name}{tex}`` attaches the plain-language note ``notes[name]`` to
    that part of its formula. ``values`` follows a drag live;
    ``committed_values`` keeps the pre-drag values until release.

    Examples:
        ```python
        from wigglystuff import FormulaDAG

        FormulaDAG(
            {
                "mu": r"\mu = \frac{1}{n}\sum_i x_i",
                "var": r"\sigma^2 = \frac{1}{n}\sum_i (x_i - \use{mu})^2",
                "sigma": r"\sigma = \sqrt{\use{var}}",
                "z": r"z_i = \frac{x_i - \use{mu}}{\note{scale}{\use{sigma}}}",
                "band": r"b = \use{mu} \pm \tangle{k}\,\use{sigma}",
            },
            parameters={"k": {"value": 2, "min_value": 0, "max_value": 4, "step": 0.5}},
            notes={"scale": "measured in standard deviations"},
        )
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    formulas = traitlets.List(traitlets.Dict()).tag(sync=True)
    layers = traitlets.List().tag(sync=True)
    routes = traitlets.List().tag(sync=True)
    parameters = traitlets.Dict(default_value={}).tag(sync=True)
    notes = traitlets.Dict(default_value={}).tag(sync=True)
    values = traitlets.Dict(default_value={}).tag(sync=True)
    committed_values = traitlets.Dict(default_value={}).tag(sync=True)
    dragging = traitlets.Bool(False).tag(sync=True)
    hovered = traitlets.Unicode("").tag(sync=True)
    legend = traitlets.Bool(True).tag(sync=True)
    selected = traitlets.Unicode("").tag(sync=True)
    theme = traitlets.Enum(["auto", "light", "dark"], default_value="auto").tag(
        sync=True
    )
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        formulas: Mapping[str, Any],
        parameters: Mapping[str, Mapping[str, Any]] | None = None,
        notes: Mapping[str, Any] | None = None,
        *,
        legend: bool = True,
        theme: str = "auto",
        **kwargs: Any,
    ) -> None:
        r"""Create a FormulaDAG widget.

        Args:
            formulas: Mapping from a formula name to its LaTeX, or to a dict
                with ``tex`` plus optional ``symbol`` (what ``\use{name}``
                renders as; defaults to the left-hand side of the first
                top-level ``=``, else the name) and ``label`` (the caption
                under the formula; defaults to the name). Reference another
                formula's output with ``\use{other_name}``.
            parameters: Draggable numbers, shared by every formula. Mark one
                with ``\tangle{name}`` and configure it exactly as in
                ``TangleLatex``: ``value`` is required; optional keys are
                ``min_value``, ``max_value``, ``step``, ``digits``,
                ``display`` (``"number"`` or ``"symbol"``), ``symbol``,
                ``label``, ``pixels_per_step``, and ``color``.
            notes: Plain-language notes, as in ``TangleLatex``. Wrap a part of
                a formula in ``\note{name}{tex}`` and map ``name`` to its text,
                or to a dict with ``text``, ``side`` (``"auto"``, ``"top"``,
                ``"bottom"``) and ``color``. Each note lives in one formula.
            legend: Show a strip under the DAG with one chip per number: its
                symbol, its ``label`` (say what it means there, e.g.
                ``"spot price"``), and its live value. Chips drag and edit
                like the numbers in the formulas, and hovering one lights up
                every place that number appears.
            theme: Color theme: ``"auto"``, ``"light"``, or ``"dark"``.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if theme not in {"auto", "light", "dark"}:
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")
        specs = _normalize_formulas(formulas)
        names = [s["name"] for s in specs]
        symbols = {s["name"]: s["symbol"] for s in specs}

        edges = []
        for spec in specs:
            for used in _USE_RE.findall(spec["tex"]):
                if used == spec["name"]:
                    raise ValueError(f"formula {used!r} cannot \\use itself.")
                if used not in symbols:
                    raise ValueError(
                        f"formula {spec['name']!r} uses unknown formula {used!r}."
                    )
                if [used, spec["name"]] not in edges:
                    edges.append([used, spec["name"]])
        cycle = _find_cycle(names, edges)
        if cycle:
            raise ValueError("formulas must not form a cycle: " + " -> ".join(cycle))

        def expand_uses(tex):
            return _USE_RE.sub(
                lambda m: rf"\htmlData{{fdag-use={m.group(1)}}}{{{symbols[m.group(1)]}}}",
                tex,
            )

        # Producers take palette colors in order; formulas nobody uses stay ink.
        producers = [n for n in names if any(src == n for src, _ in edges)]
        colors = {
            n: dict(_PRODUCER_COLORS[i % len(_PRODUCER_COLORS)]) for i, n in enumerate(producers)
        }
        normalized = []
        for spec in specs:
            split = _split_lhs(spec["tex"])
            if split:
                lhs, rest = split
                tex = rf"\htmlData{{fdag-out={spec['name']}}}{{{expand_uses(lhs)}}} ={expand_uses(rest)}"
            else:
                tex = expand_uses(spec["tex"])
            normalized.append(
                {
                    "name": spec["name"],
                    "tex": tex,
                    "label": spec["label"],
                    "color": colors.get(spec["name"], dict(_PARAM_COLOR)),
                }
            )

        params, normalized_notes = _tangle_and_notes(specs, parameters, notes)
        values = {name: spec["value"] for name, spec in params.items()}

        rows = layered_layout(dict.fromkeys(names), edges)
        layers, routes, _ = _order_and_route(names, rows, edges)
        super().__init__(
            formulas=normalized,
            layers=[layers[r] for r in sorted(layers)],
            routes=routes,
            parameters=params,
            notes=normalized_notes,
            values=values,
            committed_values=dict(values),
            legend=legend,
            theme=theme,
            **kwargs,
        )
        self._edges = [tuple(e) for e in edges]

    @traitlets.observe("values")
    def _follow_values(self, change: dict) -> None:
        # Outside a drag (e.g. a Python-side change) the committed values follow.
        if not self.dragging:
            self.committed_values = dict(self.values)

    @property
    def edges(self) -> list[tuple[str, str]]:
        """The inferred ``(producer, consumer)`` pairs."""
        return list(self._edges)

    def upstream(self, name: str) -> set[str]:
        """Every formula that ``name`` depends on, directly or transitively."""
        return self._reach(name, reverse=True)

    def downstream(self, name: str) -> set[str]:
        """Every formula that depends on ``name``, directly or transitively."""
        return self._reach(name, reverse=False)

    def _reach(self, name, *, reverse):
        if name not in {f["name"] for f in self.formulas}:
            raise ValueError(f"unknown formula {name!r}.")
        nxt = {}
        for src, dst in self._edges:
            a, b = (dst, src) if reverse else (src, dst)
            nxt.setdefault(a, []).append(b)
        seen, todo = set(), [name]
        while todo:
            for m in nxt.get(todo.pop(), []):
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        return seen
