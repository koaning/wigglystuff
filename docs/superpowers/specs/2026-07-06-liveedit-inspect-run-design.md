# LiveEdit — a top-to-bottom loop tracer

**Status:** Design approved (pending written-spec review)
**Date:** 2026-07-06

## Summary

`LiveEdit` is a new wigglystuff AnyWidget that visualizes how a Python
function's variables evolve as it runs — Bret Victor's *Inventing on Principle*
binary-search demo, with one deliberate difference: **time in a loop flows
top-to-bottom, not left-to-right.** Each pass of a loop is a new row that
appends downward, so a loop reads like a table growing down the page.

The source code sits on the left; the trace sits on the right. Hovering
anything links the two: hover a variable and every line that changes it, its
whole column, and its return light up; hover a loop and its body and table light
up. It is a teaching and debugging surface for "what did this loop actually do?"

The widget instruments **one function's body** via an AST transform, runs it to
completion, and renders the recorded trace. It does **not** descend into
functions the traced function calls — those are black boxes whose return values
are recorded but whose internals are not traced.

There is one widget class, `LiveEdit`, built around a `code → trace` pipeline.
`LiveEdit.inspect_run(fn, *args, **kwargs)` is a factory classmethod for the
read-only "inspect a run" case (scenario **A**, the v1 build target). The same
class, with `editable=True`, is the foundation for a live in-browser code editor
(scenario **B**), which is an **additive follow-up** — its contract is locked
here so it never requires a redesign, but its editor UI is out of scope for v1.

## Goals

- Reproduce the binary-search reference: code left, per-pass variable evolution
  right, flowing downward.
- Make no strong assumptions about the traced function's shape — any mix of
  sequential loops, nested loops, branches, and a return.
- Line-based, bidirectional hover linking between code and trace.
- Support arbitrary value types (numpy arrays, lists, DataFrames, objects) with
  zero hard dependencies, via `repr`.
- Light/dark theming that follows the notebook.
- An architecture where the live editor (B) is purely additive.

## Non-goals (v1)

- **The live code editor (B).** Its Python↔JS contract is fixed here; its editor
  component, debounced re-run round-trip, view/edit modes, and error-recovery UX
  are deferred. `editable` exists as a traitlet and defaults to `False`.
- **Tracing into called functions.** Calls are black boxes (see Summary).
- **Recursion visualization.** A function calling itself is a call → black box;
  only the top frame is traced.
- **Intermediate within-pass values.** We record the *end-of-pass* snapshot only
  (a variable that changes twice in one pass shows its final value for that
  pass). Confirmed during design.
- **Stepping / live playback.** The function runs to completion once; the trace
  is static (until re-run via editing in B).
- **Generators, async functions, threads.**

## Python API

```python
class LiveEdit(anywidget.AnyWidget):
    code        = traitlets.Unicode()               # source of truth
    trace       = traitlets.Dict()                  # structured per-pass repr snapshots
    annotations = traitlets.Dict()                  # AST-derived line/token map (drives hover)
    error       = traitlets.Dict(allow_none=True)   # parse / runtime / arg-mismatch, else None
    editable    = traitlets.Bool(False)             # A → False; B → True (additive)
    theme       = traitlets.Unicode("auto")         # "auto" | "light" | "dark"
    width       = traitlets.Int(...)
    height      = traitlets.Int(...)

    def __init__(self, code, *, args=(), kwargs=None, editable=False, **kw):
        # args/kwargs are stored on the instance as plain Python objects and are
        # NEVER synced to the browser. Only their reprs cross the wire.
        ...
        # trace immediately on construction.

    @traitlets.observe("code")
    def _retrace(self, change):
        # re-instrument (AST) + re-exec with the stored args → set trace / annotations / error
        ...

    @classmethod
    def inspect_run(cls, fn, *args, **kwargs):
        import inspect, textwrap
        src = textwrap.dedent(inspect.getsource(fn))
        return cls(src, args=args, kwargs=kwargs, editable=False)
```

- **A (v1):** `LiveEdit.inspect_run(binary_search, key="d", array=[...])`
  → `editable=False`, renders read-only.
- **B (later):** the same instance with `editable=True`. The frontend adds an
  editor bound to `code`; `_retrace` already fires on `code` changes, so editing
  re-runs against the original stored args. Nothing in A is removed.

`inspect_run` is the primary entry point and is re-exported from
`wigglystuff/__init__.py`. Positional and keyword args both work and seed the
setup block (`key = 'd'`, `array = [...]`) via the function's signature.

### Why args stay Python-side

The `_retrace` observer re-runs the (possibly edited) function using the stored
Python objects directly. Arbitrary args (a numpy array, a DataFrame) are not
JSON-serializable and must not be. Only the recorded `repr` strings are synced.
This is what lets B re-run edited code against the original `array=[...]` without
ever serializing it.

## Architecture

Three isolated units, each independently testable:

1. **Instrumenter** (`ast.NodeTransformer`). Parses the source, finds the target
   function (the top-level `FunctionDef` matching `fn.__name__`, else the first),
   and rewrites *its body only* to emit an **event stream** to a collector. It
   injects:
   - a **pass-boundary marker** at the top of every loop body
     (`__record_iter__(loop_id)`),
   - an **assignment record** after every assignment statement
     (`__record_assign__(loop_id_or_None, name, repr(value), lineno)`) — covering
     `Assign`, `AugAssign`, `AnnAssign`, `for`-targets, and walrus,
   - a **return record** (`__record_return__(repr(value))`).

   Instrumenting after *every assignment* (rather than only at end-of-body) makes
   the trace robust to `continue` / `break` / `return` mid-body: the end-of-pass
   snapshot is simply the last recorded value of each variable before the next
   pass boundary.

2. **Runner + collector.** Compiles the transformed AST, execs it in a fresh
   namespace to define the function, calls it with the stored args, and collects
   the event stream. A loop-context stack attributes each assignment to the
   innermost active loop (or to *setup* when outside any loop). Wraps execution
   so exceptions become an `error` payload, never a crash.

3. **Trace builder** (pure function: `events → trace dict`). Shapes the event
   stream into the structured `trace` (below). This is where the **column rule**
   and **change flags** are computed. Pure and deterministic → the main unit test
   target.

The AST is also walked once (statically) to build `annotations`: for each source
line, which tokens are which variables, which lines assign/return which variable,
and which lines are which loop's header/body (with loop ids and nesting depth).
**The frontend renders code from `annotations` + `code`; Python never ships
HTML.** This is the seam that makes B additive.

No `numpy`/`pillow`/other optional deps are imported anywhere — values become
strings via `repr` at capture time.

## Trace data model (the `trace` traitlet)

```jsonc
{
  "setup": [ {"name": "key", "repr": "'d'"}, {"name": "array", "repr": "[...]"},
             {"name": "low", "repr": "0"}, {"name": "high", "repr": "5"} ],
  "body": [
    {
      "kind": "loop",
      "loop_id": "bs",
      "loop_type": "while",          // "while" | "for"
      "columns": ["low", "high", "mid", "value"],  // only vars mutated in THIS loop
      "passes": [
        { "cells": {"low": "3", "high": "5", "mid": "2", "value": "'c'"},
          "changed": ["low", "mid", "value"] },     // assigned/changed this pass
        ...
      ],
      "children": []                 // nested loops rendered inside each pass (see below)
    }
  ],
  "returned": {"repr": "3"}          // or null if the function falls off the end
}
```

### Column rule (confirmed during design)

- A variable earns a **column** in a loop's table **only if it is assigned inside
  that loop's body** (its innermost owning loop). Variables never reassigned in
  the loop (`key`, `array`) stay in the `setup` block, not the table.
- Each row is one **pass**; each cell is the variable's **end-of-pass** `repr`.
- `changed` lists the variables actually assigned during that pass; the frontend
  emphasizes them (bold red). Unchanged columns repeat their prior value.

### Nesting

An inner loop is attached to the specific outer pass it ran under, so the outer
loop's row carries a `children` list of inner-loop trace objects. The frontend
renders these as **indented sub-tables** beneath the outer pass. Arbitrary depth
is supported by the data model; the frontend indents per level.

### Value formatting

- Values are `repr(value)` captured at assignment time. The repr string *is* the
  snapshot — no `deepcopy`, no `.copy()`; in-place mutation of a list/array can't
  corrupt earlier rows.
- Change detection is **string comparison** of consecutive reprs — sidesteps
  numpy's ambiguous `==` entirely and works uniformly for arrays, lists, dicts,
  DataFrames.
- Long reprs are truncated **for display only** (CSS ellipsis) with the full repr
  in a hover tooltip.
- Known minor edge case: numpy self-truncates large-array reprs, so two different
  huge arrays can share a truncated repr and read as "unchanged." Acceptable;
  not special-cased.

## Rendering & layout (frontend)

Two-column card: **code left, trace right** (matching the reference).

- **Setup block** — a key/value list of parameters and pre-loop assignments,
  shown once at the top of the trace.
- **Loop tables** — one per loop, stacked down the page. A badge marks the loop
  type: `for` (blue) vs `while` (purple). Columns are the loop's mutated
  variables; rows are passes, appended downward. Value cells stay light for
  readability; row label and a trailing spacer column stay transparent.
- **Nested loops** — indented sub-tables beneath the owning outer pass.
- **Return chip** — the returned value at the bottom.

Multiple sequential loops → multiple stacked tables. A function with no loops →
just the setup block and return chip.

## Interaction model (frontend)

**Selection is line-based.** Every row — a code line, a key/value row, a loop's
pill row, a table row — is one hover target spanning the **full width** of its
panel. Pointing anywhere along a row's height selects that row's subject; a more
specific token inside the row (a variable name, a table cell) *refines* the
selection. Implemented as a single delegated hover resolver, not per-element
hover zones.

Two highlight colors, each with one meaning; a third color is reserved for data:

- **Yellow = a variable.** Its name everywhere it appears, the lines that
  assign/return it, its table column, and the return chip. Bidirectional: hover
  the name, a cell, the column header, or the chip — all light the same set.
- **Green = a loop.** Its body lines in the code and its table(s). Because one
  loop in the code can run many times (an inner loop re-runs each outer pass),
  hovering it lights **all** its table instances. Nesting is shown by **opacity
  stacking**: the green tint is translucent, so an inner region under an outer
  region reads darker — no borders, no rounded corners.
- **Red = "changed this pass."** Data emphasis on changed cells, not a hover
  state.

Hovering **inside a table** lights **both**: the variable (yellow column) and its
owning loop(s) (green, stacked for depth) — a cell is literally a value produced
by a loop pass for a variable.

## Error handling

`error` is a dict (or `None`). It is set — and the trace panel shows a clear
message instead of crashing — for:

- **Parse errors** (`SyntaxError`) — `{type, message, lineno}`.
- **Runtime exceptions** during the traced run — `{type, message, lineno}`; any
  partial trace collected before the exception is still rendered.
- **Argument mismatch** — the stored args no longer fit the (edited) signature
  → a clear "arguments don't match" message. (Matters mainly for B, but the
  guard lives in `_retrace` from day one.)

## Un-traceable inputs

`inspect_run` raises a clear `TypeError`/`ValueError` (not a cryptic
`OSError`) when it cannot get usable source:

- **Builtins / C-level functions** (no Python source).
- **Lambdas** (source is ambiguous / not a `def`).
- **Interactively-defined functions** where `inspect.getsource` fails.

Documented limitations (work best with plain top-level `def`s): decorated
functions (the decorator must be importable in the re-exec namespace) and
closures with free variables from an enclosing scope (not available on re-exec).

## Repo integration checklist

- `wigglystuff/live_edit.py` (class `LiveEdit`); JS in `js/live-edit/`, built to
  `wigglystuff/static/liveedit.js` + `liveedit.css`.
- Re-export `LiveEdit` (and `inspect_run`) from `wigglystuff/__init__.py`.
- Add to the agent table in `AGENTS.md`/`CLAUDE.md`.
- Gallery: `docs/index.md`, `README.md`, `docs/llms.txt`; screenshot in
  `docs/assets/gallery/` as `.webp`.
- `CHANGELOG.md` under `## [Unreleased]`.
- Demo notebook `demos/liveedit.py` (PEP 723 header); MoLab link carries
  `?utm_source=wigglystuff`.
- Reference page `docs/reference/live-edit.md`.

## Testing (tight)

1. **Trace builder — binary search.** `inspect_run(binary_search, key="d",
   array=list("abcdef"))` produces the expected columns (`low, high, mid,
   value`), three passes, correct end-of-pass reprs and `changed` flags, and
   `returned.repr == "3"`.
2. **repr-based change detection with a numpy array.** A loop that mutates a
   numpy array in place records distinct per-pass reprs (proving snapshot-by-repr
   works) and never raises numpy's ambiguous-truth error. Skipped if numpy absent.
3. **Nested loops.** `grid_sum(rows=2, cols=3)` yields an outer loop whose passes
   carry inner-loop `children` with the correct `total` progression.
4. **Un-traceable input.** `inspect_run(len)` raises a clear error, not `OSError`.

Per repo convention, also smoke-test with `uv run python -c "..."` and validate
the demo with `uv run marimo check demos/liveedit.py` and `uv run demos/liveedit.py`.

## Deferred (B — live editor, contract locked here)

When built, B adds only:

- An editable code buffer bound to `code` (CodeMirror-style), debounced.
- A **view/edit mode**: view = annotated + hoverable (A's renderer); edit = plain
  text (no per-token hover, since annotations require a valid parse); on a valid
  parse+run it flips back to the refreshed annotated view.
- Rendering of the `error` payload during broken states.

Unchanged from A: the `code → trace/annotations/error` pipeline, the trace model,
the annotation model, the renderer, and the hover model.
