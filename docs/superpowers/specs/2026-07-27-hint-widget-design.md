# Hint — an arrow and a note pointing at a widget

**Status:** Design approved (pending written-spec review)
**Date:** 2026-07-27

## Summary

`Hint` wraps a live widget and draws a curved arrow from an explanatory note to
the widget's edge. It lets a notebook author annotate the notebook itself —
"drag this to change N" — so a reader knows what to interact with and why.

```python
import marimo as mo
from wigglystuff import Hint

slider = mo.ui.slider(1, 10, label="N")
Hint(slider, "drag to change **N**")
```

It is a **marimo-only display helper**, not an AnyWidget. It follows the
`WidgetDAG` pattern: the wrapped widget and the note are laid out as two
light-DOM boxes, and a contentless 0×0 AnyWidget escapes its own shadow root to
draw an SVG arc between them in a shared coordinate space.

## Goals

- One arrow, one note, attached to one widget.
- The note is **anything marimo can render** — a markdown string, `mo.md`,
  `mo.image`, a figure, even another widget.
- The arc colour is configurable.
- Placement on any of the four sides.
- Zero new dependencies and no JS build step.

## Non-goals

- **Reactive note text.** The note is static, written once by the author. A
  reactive f-string is a natural later addition but is not designed for here.
- **Pointing at widget internals** (a slider handle, a chart legend). The arrow
  lands on the wrapped widget's bounding box. Reaching into another widget's
  shadow root would couple `Hint` to that widget's private DOM.
- **Jupyter support.** Raises a clear `RuntimeError` outside a marimo kernel.
- **Styling the note.** Only the arc has a `color`. The note inherits the
  notebook's text colour; authors style it with markdown or inline HTML.

## Python API

```python
Hint(
    target,               # anything marimo can render
    note,                 # str -> mo.md(str); anything else rendered as-is
    *,
    side="right",         # "left" | "right" | "top" | "bottom"
    color="currentColor", # arc and arrowhead only; inherits notebook text colour
    gap=3,                # marimo stack gap between target and note
)
```

- `target` — the widget being annotated. Passed through `mo.as_html`.
- `note` — a `str` is rendered with `mo.md(...)`, so markdown, LaTeX, and links
  work for free. Any other object is rendered as-is via `mo.as_html`.
- `side` — where the note sits relative to the target. Validated; anything else
  raises `ValueError`.
- `color` — any CSS colour string. Applies to the arc stroke and the arrowhead.
  Defaults to `currentColor`, so the arc adopts the notebook's own text colour
  and follows a light/dark theme switch with no CSS of our own.
- `gap` — spacing between the two boxes, in marimo stack-gap units (the same
  units as `WidgetDAG`'s `mo.hstack(..., gap=6)`). The arc needs some clear
  space to live in, so this is the one geometry knob worth exposing.

No `.value`, no traitlets on the public object, no `.observe`. `Hint` is a
display helper; the wrapped widget stays the thing you read.

## Architecture

Two pieces in `wigglystuff/hint.py`, mirroring `wigglystuff/widget_dag.py`:

### `Hint` — the display helper

A plain Python class implementing `_mime_()`, returning `("text/html", html)`
(plus `_repr_mimebundle_()` purely to convert Jupyter's silent plain-text repr
into a clear error, as `WidgetDAG` does at `widget_dag.py:286`).

**`_mime_` rather than `_display_`.** `mo.as_html` short-circuits on
`isinstance(value, Html)` and otherwise consults `get_formatter`, which honours
`_mime_`. So a `Hint` composes into `mo.hstack`, `mo.vstack`, an `mo.md`
f-string, a `.callout()`, or another `Hint`.

Note that `_display_` would *also* have composed — `get_formatter` handles it at
`marimo/_output/formatting.py:175`, so `WidgetDAG` is embeddable too despite
implementing only `_display_`. `_mime_` is preferred here for two narrower
reasons: it returns the HTML string directly, skipping the extra
`<marimo-mime-renderer>` layer that the `_display_` path wraps output in, and it
gives an obvious place to cache the built HTML so the inner `_Arc` keeps a stable
identity across re-renders.

Subclassing `mo.Html` would achieve the same thing — it is what `mo.md` itself
does (`class _md(Html)`) — but marimo is **not** a wigglystuff dependency (not
even an optional one), and a module-level base class would require it at import
time, breaking `import wigglystuff` for everyone else. Every marimo import in
this module is therefore function-local, matching the rest of the package.

The built HTML is cached on first `_mime_()` call so the inner `_Arc` widget
keeps a stable identity across re-renders.

`_build_html()` produces:

```html
<div data-hint-root style="position:relative;display:inline-block">
  <!-- mo.hstack / mo.vstack of: -->
  <div data-hint-box="target">…mo.as_html(target)…</div>
  <div data-hint-box="note">…mo.as_html(note)…</div>
  <!-- plus the 0×0 overlay widget -->
</div>
```

`side` decides both the stack direction (`mo.hstack` for left/right,
`mo.vstack` for top/bottom) and the box order.

The two boxes are wrapped with `mo.Html`, not `mo.md`: they are already HTML, so
there is no markdown to run. The outer root is a plain f-string returned straight
from `_mime_`, so no markdown pass touches it either.

**Both boxes interpolate `mo.as_html(x).text`, never `x` directly.** `mo.md`
returns a `marimo._output.md._md` whose `__format__` yields the *original
markdown source* rather than rendered HTML — deliberate, so `mo.md` nests inside
another `mo.md` f-string. But a raw HTML block like `<div data-hint-box=…>` has
its contents left unprocessed by the markdown pass, so a plain `{note}` renders
literal `**bold**`. `WidgetDAG` never hits this because it only wraps widgets,
whose `__format__` does return `.text`.

The marimo guard reuses the approach of `_require_marimo_notebook()` in
`wigglystuff/widget_dag.py:45` — same `mo.running_in_notebook()` check, with the
message naming `Hint`.

### `_Arc(anywidget.AnyWidget)` — the overlay

Contentless. Traits `side` (Unicode) and `color` (Unicode), both `sync=True`.
`_esm = Path(__file__).parent / "static" / "hint.js"`. No `_css`: there is
nothing to theme, since the arc colour is a trait and the note inherits the
notebook's text colour.

### `wigglystuff/static/hint.js`

Hand-written unminified ESM, no npm dependency, no `Makefile` target. Style B
(clean curve) needs no drawing library.

It follows the `static/widget-dag.js:53-70` playbook verbatim:

1. `const host = el.getRootNode().host || el` — climb out of the
   `<marimo-anywidget>` shadow root.
2. Collapse the host to `position:absolute; width:0; height:0` so it occupies no
   layout space.
3. `host.closest("[data-hint-root]")` to find the light-DOM container.
4. Append an SVG with `position:absolute; left:0; top:0; width:100%; height:100%;
   pointer-events:none; overflow:visible` into that container, so the SVG and
   the two boxes share one coordinate space.
5. Measure both `[data-hint-box]` rects relative to `root.getBoundingClientRect()`.
   Because hints nest, the lookup keeps only boxes this root owns directly —
   `[...root.querySelectorAll(…)].find(b => b.closest("[data-hint-root]") === root)`
   — otherwise an outer root would measure an inner hint's boxes.
6. Redraw on `requestAnimationFrame`, `setTimeout(80)`, `setTimeout(400)`,
   `new ResizeObserver(draw).observe(root)`, and `img` `load` listeners. No
   scroll listener is needed because all coordinates are root-relative.

Also re-render on `change:color` and `change:side`.

## Geometry

One quadratic bezier per hint. For `side="right"` (note to the right of target):

- **start** `p0 = (note.left - 4, note.cy)`
- **end** `p2 = (target.right + 5, target.cy)`
- **control** `p1` = chord midpoint pushed perpendicular to the chord by
  `clamp(0.14 × |chord|, 8, 26)` px, so short hops stay gentle and long ones do
  not balloon.

The other three sides use the same formula with axes swapped (top/bottom) or
signs flipped (left).

**Arrowhead.** Drawn as an explicit two-stroke chevron path at `p2`, oriented
along the end tangent, which for a quadratic bezier is simply `p2 - p1`.

This deliberately departs from `widget-dag.js:69`, which uses an SVG `<marker>`
with a hardcoded `id="wdag-ah"` and a hardcoded `#9aa0a6` stroke. Because
`color` is per-instance here and two hints can coexist in one notebook, a shared
global marker `id` in the light DOM would collide. An explicit path is a few
lines of arithmetic and removes that bug class entirely.

## Error handling

- `side` not in the four allowed values → `ValueError` at construction.
- Displayed outside a running marimo notebook → `RuntimeError` from both
  `_display_()` and `_repr_mimebundle_()`.
- JS: if `[data-hint-root]` is not found, return without drawing rather than
  throwing — same defensive early-return as `widget-dag.js:61`.
- JS: if either `[data-hint-box]` is missing, skip the draw.

## Tests

Kept to three, in `tests/test_hint.py`:

1. **Constructor** — the happy path stores `side`, `color`, and `gap`; an
   invalid `side` raises `ValueError`.
2. **Runtime guard** — outside a marimo kernel, both `_mime_()` and
   `_repr_mimebundle_()` raise `RuntimeError`. `side` is validated *before* the
   guard, so case 1 stays testable without a kernel.
3. **Note rendering and composition** — a `str` note and an `mo.md` note both
   render their markdown (the `__format__` trap above); the HTML carries both
   `data-hint-box` markers; and `mo.as_html`, an `mo.hstack` of two hints, and a
   nested `Hint(Hint(...))` each produce the expected number of
   `data-hint-root` elements.

## Registration checklist

Per `agents.md`:

- Export `Hint` in `wigglystuff/__init__.py` (import and `__all__`).
- `docs/reference/hint.md`.
- `demos/hint.py` — a marimo demo notebook.
- Gallery rows in `docs/index.md`, `README.md`, and `docs/llms.txt`, with
  `?utm_source=wigglystuff` on the MoLab link.
- `CHANGELOG.md` under `## [Unreleased]`, a few tight bullets.
- A `.webp` screenshot in `docs/assets/gallery/` (drop a PNG in and run
  `uv run python scripts/png_to_webp.py`).
- Add the `Hint` row to the agent table in `agents.md` (`CLAUDE.md` is a symlink
  to it; stage `agents.md`).

## Verification

1. `uv run python -c "..."` — construct a `Hint`, check `side` validation and
   that the `RuntimeError` fires outside marimo.
2. `uv run marimo check demos/hint.py` — structure and cell dependencies.

   Note that `uv run demos/hint.py` **cannot** validate this demo. That is marimo
   *script* mode, where `mo.running_in_notebook()` is False and the guard fires
   by design. `running_in_notebook()` is True for any `KernelRuntimeContext`, so
   both `marimo edit` and `marimo run` (deployed app mode) work fine. `WidgetDAG`
   behaves identically — this is inherent to marimo-only display helpers, not a
   defect.
3. `marimo edit demos/hint.py` — **visual approval gate.** Confirm the arc lands
   on the widget edge, all four `side` values place correctly, `color` applies to
   arc and arrowhead, a markdown note renders, and two hints in one notebook do
   not interfere. Also resize the window to confirm the `ResizeObserver` redraw.
4. `uv run pytest tests/test_hint.py` after visual approval.

Per `agents.md`, stop at step 3 for visual approval before running the wider
suite, updating galleries, or committing.

## Rejected alternatives

- **Visual style.** Four directions were mocked up and rendered: sketchy
  hand-drawn marginalia (needs rough.js plus a system handwriting font), the
  clean curve, a speech bubble with a pointer tail (no connector, effectively a
  tooltip), and a technical leader line (edge dot plus hairline rule). The clean
  curve was chosen: it matches the arrows `WidgetDAG` already draws, keeping the
  repo visually coherent, and needs no dependency.
- **Naming.** `Annotate` collides with the existing `AnnotationWidget` in
  `wigglystuff/annotation.py` (an unrelated data-labelling input panel), and
  `annotate.py` next to `annotation.py` invites mis-edits. `Callout` leans
  toward the rejected speech-bubble reading. `Gloss` is precise but
  undiscoverable. `PointAt`, `ArrowNote`, `SideNote`, and `Leader` were also
  considered. `Hint` won: short, states the intent, and unused anywhere in the
  codebase.
- **`DriverTour` as the base.** Wrong model. It is a sequential, button-gated
  tour using body-appended fixed-position overlays and global CSS selectors, so
  it cannot even reach elements inside another widget's shadow root.
