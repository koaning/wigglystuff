# LatexTangle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a KaTeX-backed AnyWidget whose named numeric parameters can be dragged or typed directly inside a formula, with numeric/symbolic presentation, repeated references, theme-aware colors, reset, and optional reveal-all-symbols-on-drag behavior.

**Architecture:** Python validates and normalizes a `latex` template plus a `parameters` mapping, then exposes `values` as the only live synced value mapping. The browser replaces `\tangle{name}` markers with narrowly trusted KaTeX `\htmlData` wrappers, delegates pointer/editing events from a stable host, and clones `values` on every model update so traitlets synchronization fires reliably.

**Tech Stack:** Python 3.11+, AnyWidget, traitlets, vanilla JavaScript/CSS, KaTeX 0.17.0 from jsDelivr, marimo, pytest, Playwright.

## Global Constraints

- Public class name: `LatexTangle`; module: `wigglystuff.latex_tangle`.
- Public synced traitlets: `latex`, `parameters`, `values`, `display_mode`, `editor`, `reveal_all_on_drag`, `error`.
- Parameter display values are `"number"` and `"symbol"`; colors accept a CSS string or `{light, dark}` mapping.
- `reveal_all_on_drag=False` reveals only the selected symbolic parameter; `True` reveals every symbolic parameter after the pointer crosses the drag threshold.
- Click-to-type reveals only the selected parameter regardless of `reveal_all_on_drag`.
- The widget includes Reset but no range/step footer.
- Theme styles respond to `prefers-color-scheme`, `.dark`, `.dark-theme`, and `[data-theme="dark"]`.
- KaTeX loads from a pinned CDN; do not change `package-lock.json`.

---

### Task 1: Python API and validation

**Files:**
- Create: `tests/test_latex_tangle.py`
- Create: `wigglystuff/latex_tangle.py`
- Modify: `wigglystuff/__init__.py`

**Interfaces:**
- Consumes: `LatexTangle(latex, parameters, *, display_mode=True, editor="popover", reveal_all_on_drag=False)`.
- Produces: normalized JSON-safe `parameters`, live `values`, and package-root import `from wigglystuff import LatexTangle`.

- [ ] Write tests covering multiple parameters, repeated markers, default and explicit colors, string-color shorthand, both display modes, synced values, and all invalid configurations.
- [ ] Run `uv run --extra test pytest tests/test_latex_tangle.py -q` and confirm collection/import fails because `LatexTangle` does not exist.
- [ ] Implement normalization and validation: conservative marker names, exact marker/config key agreement, finite numeric values, ordered bounds, positive step, non-negative digits, valid display/editor values, and light/dark color pairs.
- [ ] Re-run the focused tests and confirm they pass.

### Task 2: KaTeX frontend and browser behavior

**Files:**
- Create: `wigglystuff/static/latex-tangle.js`
- Create: `wigglystuff/static/latex-tangle.css`
- Create: `tests/fixtures/latex_tangle_test_notebook.py`
- Create: `tests/test_e2e/test_latex_tangle_browser.py`

**Interfaces:**
- Consumes: normalized parameter records and `values` from Task 1.
- Produces: drag/edit/reset interactions and `error` reporting.

- [ ] Write Playwright tests for multiple independent numeric parameters, repeated-symbol updates, `reveal_all_on_drag`, selected-only reveal, click-to-type, reset, configured light/dark colors, and absence of range metadata.
- [ ] Run the focused browser test and confirm it fails because the frontend assets do not exist.
- [ ] Implement the KaTeX renderer, `\tangle{name}` expansion, delegated pointer lifecycle, drag threshold, snapping/clamping, cloned `values` updates, debounced model saves with a final flush, popover/inline editing, and reset-to-constructor-values.
- [ ] Implement scoped light/dark CSS with per-target custom properties and no slider metadata footer.
- [ ] Re-run the focused browser test and confirm it passes without console errors.

### Task 3: Demo and public documentation

**Files:**
- Create: `demos/latex_tangle.py`
- Create: `docs/reference/latex-tangle.md`
- Create: `docs/assets/gallery/latex-tangle.webp`
- Modify: `docs/index.md`, `docs/reference/index.md`, `docs/llms.txt`, `readme.md`, `CHANGELOG.md`, `AGENTS.md`

**Interfaces:**
- Demo shows numeric mode, selected-only symbolic mode, and `reveal_all_on_drag=True`, with Python reading `widget.values`.

- [ ] Add the marimo demo using the exact public constructor and a repeated-symbol formula.
- [ ] Run `uv run marimo check demos/latex_tangle.py` and execute the notebook with the local editable package.
- [ ] Capture the running widget, convert the PNG with `uv run python scripts/png_to_webp.py`, and use `latex-tangle.webp` in both galleries.
- [ ] Add root/reference docs, the required MoLab UTM links, the quick-reference row, and an `Unreleased` changelog entry.

### Task 4: Final verification

**Files:** all files above.

- [ ] Run the Python unit tests, import tests, and focused Playwright test.
- [ ] Smoke-test construction, trait changes, repeated markers, reset state, and invalid inputs with `uv run python -c "..."`.
- [ ] Run `uv run marimo check demos/latex_tangle.py` and execute every demo cell.
- [ ] Run `make docs`, `git diff --check`, and confirm `package-lock.json` is unchanged.
- [ ] Inspect the final gallery screenshot in both light and dark themes and summarize exact verification evidence.
