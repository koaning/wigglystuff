# FormulaDAG static rendering — design

## Goal

FormulaDAG is often wanted as a static artifact: a diagram to read, not a
widget to play with. Two surfaces:

1. **In-notebook readonly** — same AnyWidget, all input handlers off.
2. **Static HTML export** — a self-contained `.html` file reusing the existing
   frontend, for docs/blog posts/attachments.

## Decisions (from brainstorming)

- Export form: self-contained HTML file; KaTeX still loads from the same
  jsdelivr CDN URL the widget uses (export needs internet for math fonts).
- Notebook static: an `interactive` trait on the widget, not a separate
  display helper.
- Export is always static, regardless of the widget's `interactive` value.

## Python API (`wigglystuff/formula_dag.py`)

- `interactive = traitlets.Bool(True).tag(sync=True)` — constructor kwarg
  `interactive: bool = True`.
- `dag.static() -> FormulaDAG` — sets `interactive = False`, returns `self`
  (supports `FormulaDAG(...).static()` and later toggling).
- `dag.to_html(title: str | None = None) -> str` — full `<!doctype html>` doc.
- `dag.save(path) -> Path` — writes `to_html()` (UTF-8), returns the Path.

`to_html()` serializes the synced traits the renderer reads
(`formulas, layers, routes, parameters, notes, values, outputs,
output_errors, legend, theme, selected, hovered, error`) plus
`interactive: false`, JSON-escapes `<`, and emits:

- `<style>` with `static/formula-dag.css` inlined
- `<div id="fd-root">`
- `<script type="module">` with `static/formula-dag.js` inlined, then a
  bootstrap: a ~30-line shim model (`get/set/on/off/save_changes` over a plain
  object, `set` fires `change:<key>`) and
  `render({ model, el: document.getElementById("fd-root") })`.

No new synced traits beyond `interactive`; no Python-side LaTeX rendering.

## JS (`wigglystuff/static/formula-dag.js`)

- `const isInteractive = () => model.get("interactive") !== false;`
  (undefined ⇒ true, so older states/widget calls are unaffected).
- `applyInteractive()` toggles `formula-dag--static` on the root; called from
  `build()` and on `change:interactive`.
- Handlers stay attached but early-return when not interactive (so live
  toggling works without re-render): card `mouseenter/mouseleave/click`,
  `handleHover`, `setHovered`, `startDrag`, `handleKeydown`, `handleReset`.
- Legend chip `aria-label` drops the "Drag horizontally or press Enter"
  hint when static.

## CSS (`wigglystuff/static/formula-dag.css`)

`.formula-dag--static` rules: default cursor on cards/chips/params, no card
`:hover` background, no param `:hover/:focus-visible` highlight, hide the
Reset button, drop the dotted underline on `[data-tangle-param]`.

## Tests (`tests/test_formula_dag.py`)

- `interactive` defaults True; `static()` flips it and returns self.
- `to_html()` contains doctype, serialized state (formula names, values),
  inlined module script, `interactive: false`; no `</script>` breakage.
- `save()` writes a file that round-trips `to_html()`.
