"""FormulaDAG -- a DAG of LaTeX formulas, wired by where each output is used."""

from __future__ import annotations

import inspect
import math
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
from .widget_dag import _order_and_route

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
        fn = raw.get("fn")
        if fn is not None and not callable(fn):
            raise ValueError(f"formula {name!r} fn must be callable.")
        digits = raw.get("digits", 3)
        if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
            raise ValueError(f"formula {name!r} digits must be a non-negative integer.")
        row = raw.get("row", 0)
        if isinstance(row, bool) or not isinstance(row, int) or row < 0:
            raise ValueError(f"formula {name!r} row must be a non-negative integer.")
        out.append(
            {
                "name": name,
                "tex": tex,
                "symbol": symbol,
                "label": label,
                "fn": fn,
                "digits": digits,
                "row": row,
            }
        )
    return out


def _formula_rows(names, edges, min_rows):
    """Give each formula a row (0 = top): one below the deepest formula it uses.

    Formulas that use nothing share the top row. ``min_rows`` pushes a formula
    down to at least that row, and everything that uses it follows, so a
    minimum can never put a formula above one it uses.
    """
    parents = {n: [] for n in names}
    for src, dst in edges:
        parents[dst].append(src)
    rows = {}

    def row_of(n):
        if n not in rows:
            below = 1 + max((row_of(p) for p in parents[n]), default=-1)
            rows[n] = max(min_rows.get(n, 0), below)
        return rows[n]

    for n in names:
        row_of(n)
    return rows


def _fn_arguments(specs, parameter_names):
    """Map each formula with an ``fn`` to the names its arguments read.

    An argument reads the parameter or formula of the same name (a default
    makes it optional). Formula arguments must not form a cycle.
    """
    formula_names = {s["name"] for s in specs}
    args = {}
    for spec in specs:
        fn = spec["fn"]
        if fn is None:
            continue
        name = spec["name"]
        try:
            signature = inspect.signature(fn)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"formula {name!r} fn must have inspectable arguments.") from exc
        names = []
        for arg in signature.parameters.values():
            if arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                raise ValueError(f"formula {name!r} fn cannot take *args or **kwargs.")
            known = (arg.name in parameter_names) + (arg.name in formula_names)
            if known == 2:
                raise ValueError(
                    f"formula {name!r} fn argument {arg.name!r} is both a parameter "
                    "and a formula name; rename one."
                )
            if known == 0:
                if arg.default is not arg.empty:
                    continue
                raise ValueError(
                    f"formula {name!r} fn argument {arg.name!r} is not a parameter "
                    "or formula name."
                )
            names.append(arg.name)
        args[name] = names
    deps = [[a, n] for n, names in args.items() for a in names if a in formula_names]
    cycle = _find_cycle(sorted(formula_names), deps)
    if cycle:
        raise ValueError("formula fns must not form a cycle: " + " -> ".join(cycle))
    return args


def _fn_inputs(fn_args, param_names):
    """Map each formula with an ``fn`` to the parameters its value depends on.

    Follows formula arguments transitively: if ``d2`` reads ``d1`` and ``d1``
    reads ``T``, then ``d2`` depends on ``T``.
    """
    inputs = {}

    def collect(name):
        if name not in inputs:
            found = set()
            for arg in fn_args[name]:
                if arg in param_names:
                    found.add(arg)
                elif arg in fn_args:
                    found |= collect(arg)
            inputs[name] = found
        return inputs[name]

    for name in fn_args:
        collect(name)
    return {name: sorted(found) for name, found in inputs.items()}


def _whole_note(tex: str) -> str | None:
    """Return ``name`` when ``tex`` is exactly one ``\\note{name}{...}``, else ``None``."""
    tex = tex.strip()
    m = _NOTE_RE.match(tex)
    if not m or tex[m.end() : m.end() + 1] != "{":
        return None
    return m.group(1) if _strip_notes(tex) == tex[m.end() + 1 : -1] else None


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
    outputs = traitlets.Dict(default_value={}).tag(sync=True)
    committed_outputs = traitlets.Dict(default_value={}).tag(sync=True)
    output_errors = traitlets.Dict(default_value={}).tag(sync=True)
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
                formula's output with ``\use{other_name}``. Add ``fn`` to
                compute the formula's value live: a callable whose argument
                names pick parameters or other formulas, e.g.
                ``"fn": lambda d1, vol: d1 - vol``. The value shows in the
                legend and, while you drag or type a number it depends on,
                in place of the formula's symbol and its uses (rounded to
                ``digits``, default 3). It lands in ``outputs``;
                ``committed_outputs`` holds the pre-drag values, like
                ``committed_values``. By default each formula sits one row
                below the deepest formula it uses, so formulas that use
                nothing share the top row. Add ``row`` (0 is the top) to push
                a formula down to at least that row; the formulas that use it
                move down with it.
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

        params, normalized_notes = _tangle_and_notes(specs, parameters, notes)
        values = {name: spec["value"] for name, spec in params.items()}
        self._fns = {s["name"]: s["fn"] for s in specs if s["fn"] is not None}
        self._fn_args = _fn_arguments(specs, set(params))
        inputs = _fn_inputs(self._fn_args, set(params))
        outputs, output_errors = self._compute(values)

        # Producers take palette colors in order; formulas nobody uses stay ink.
        # The browser expands \use{...} and the output symbol itself, so it can
        # swap in live values while a number they depend on changes.
        producers = [n for n in names if any(src == n for src, _ in edges)]
        colors = {
            n: dict(_PRODUCER_COLORS[i % len(_PRODUCER_COLORS)]) for i, n in enumerate(producers)
        }
        normalized = []
        for spec in specs:
            split = _split_lhs(spec["tex"])
            lhs, body = (split[0], split[1]) if split else ("", spec["tex"])
            normalized.append(
                {
                    "name": spec["name"],
                    "lhs": lhs,
                    "tex": body,
                    "out_note": _whole_note(lhs) if lhs else None,
                    "inputs": inputs.get(spec["name"], []),
                    "label": spec["label"],
                    "symbol": spec["symbol"],
                    "digits": spec["digits"],
                    "has_fn": spec["fn"] is not None,
                    "color": colors.get(spec["name"], dict(_PARAM_COLOR)),
                }
            )

        rows = _formula_rows(names, edges, {s["name"]: s["row"] for s in specs})
        layers, routes, _ = _order_and_route(names, rows, edges)
        super().__init__(
            formulas=normalized,
            layers=[layers[r] for r in sorted(layers) if layers[r]],
            routes=routes,
            parameters=params,
            notes=normalized_notes,
            values=values,
            committed_values=dict(values),
            outputs=outputs,
            committed_outputs=dict(outputs),
            output_errors=output_errors,
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
        if self._fns:
            self.outputs, self.output_errors = self._compute(self.values)

    @traitlets.observe("committed_values")
    def _follow_committed(self, change: dict) -> None:
        if self._fns:
            self.committed_outputs, _ = self._compute(self.committed_values)

    def _compute(self, values: Mapping[str, float]) -> tuple[dict, dict]:
        """Evaluate every ``fn`` in dependency order.

        Returns ``(outputs, errors)``. A formula whose ``fn`` raises, returns
        something that isn't a finite number, or reads a formula without a
        value gets ``None``; the exception message goes in ``errors``.
        """
        outputs: dict[str, float | None] = {}
        errors: dict[str, str] = {}

        def value_of(name):
            if name not in outputs:
                kwargs = {}
                for arg in self._fn_args[name]:
                    kwargs[arg] = values[arg] if arg in values else (
                        value_of(arg) if arg in self._fns else None
                    )
                if any(v is None for v in kwargs.values()):
                    outputs[name] = None
                    return None
                try:
                    result = float(self._fns[name](**kwargs))
                    outputs[name] = result if math.isfinite(result) else None
                except Exception as exc:  # report it, keep the rest of the DAG live
                    errors[name] = f"{type(exc).__name__}: {exc}"
                    outputs[name] = None
            return outputs[name]

        for name in self._fns:
            value_of(name)
        return outputs, errors

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
