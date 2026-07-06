# GridDraw Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `GridDraw` AnyWidget described in `docs/superpowers/specs/2026-07-06-griddraw-widget-design.md`.

**Architecture:** `GridDraw` follows the existing wigglystuff widget pattern: a small Python `anywidget.AnyWidget` wrapper with synced traitlets and validation, a vanilla SVG frontend, checked-in static JS/CSS, a marimo demo, and generated-doc reference stubs. Python owns input validation and helper methods; the frontend owns drawing, erasing, undo, clear, theme toggling, and width picker behavior.

**Tech Stack:** Python 3.10+, anywidget, traitlets, vanilla JavaScript, SVG, CSS, esbuild, marimo, pytest.

## Global Constraints

- Work only inside `/Users/vincentwarmerdam/Development/wigglystuff/.conductor/minnetonka-v3`.
- Do not touch `/Users/vincentwarmerdam/Development/wigglystuff`.
- Target branch for comparison is `origin/main`.
- Keep `package-lock.json` unchanged unless intentionally updating JS dependencies.
- `rows` and `cols` count cells; valid intersections are `0..rows` and `0..cols`.
- Dots are `[[row, col], ...]`; lines are `[{"from": [r, c], "to": [r, c], "width": int}, ...]`.
- Lines must be orthogonally adjacent unit segments; no diagonals.
- Use theme-aware default ink; colors are out of scope for v1.
- Every MoLab link must include `?utm_source=wigglystuff`.

---

### Task 1: Python API and Validation

**Files:**
- Create: `tests/test_grid_draw.py`
- Create: `wigglystuff/grid_draw.py`
- Modify: `wigglystuff/__init__.py`

**Interfaces:**
- Produces: `GridDraw(rows=8, cols=8, line_width=2, dot_radius=6, theme=None, width=440, height=440)`
- Produces: `GridDraw.add_dot(row: int, col: int) -> None`
- Produces: `GridDraw.add_line(a: tuple[int, int], b: tuple[int, int], width: int | None = None) -> None`
- Produces: `GridDraw.clear() -> None`

- [ ] Write failing tests for defaults, constructor validation, idempotent `add_dot`, canonical/idempotent `add_line`, invalid line endpoints, `line_width` int/list validation, and `clear()`.
- [ ] Run `uv run pytest tests/test_grid_draw.py -q`; expected failure: `ImportError` or missing `GridDraw`.
- [ ] Implement `wigglystuff/grid_draw.py` with traitlets, validation helpers, canonical segment storage, and helper methods.
- [ ] Export `GridDraw` in `wigglystuff/__init__.py`.
- [ ] Run `uv run pytest tests/test_grid_draw.py -q`; expected pass.

### Task 2: Frontend Assets

**Files:**
- Create: `js/grid-draw/widget.js`
- Create: `wigglystuff/static/griddraw.css`
- Create: `wigglystuff/static/griddraw.js`
- Modify: `package.json`

**Interfaces:**
- Consumes: synced `dots`, `lines`, `rows`, `cols`, `line_width`, `dot_radius`, `theme`, `width`, `height`.
- Produces: SVG interaction layer that updates `dots`, `lines`, and `theme` via `model.set(...)` and `model.save_changes()`.

- [ ] Add `build-griddraw` and `dev-griddraw` scripts to `package.json`.
- [ ] Implement `js/grid-draw/widget.js` with mode toolbar, width picker, SVG rendering order, point/segment hit detection, drag painting, eraser, snapshot undo, clear, `Cmd/Ctrl+Z`, and model change listeners.
- [ ] Implement `wigglystuff/static/griddraw.css` with scoped light/dark variables and compact toolbar styling.
- [ ] Run `npm run build-griddraw`; expected: `wigglystuff/static/griddraw.js` generated without modifying `package-lock.json`.

### Task 3: Demo and Documentation

**Files:**
- Create: `demos/griddraw.py`
- Create: `docs/reference/grid-draw.md`
- Create: `docs/assets/gallery/griddraw.webp`
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/llms.txt`
- Modify: `docs/reference/index.md`
- Modify: `CHANGELOG.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: `GridDraw` public API from Task 1.
- Produces: marimo demo and docs entries with MoLab links containing `?utm_source=wigglystuff`.

- [ ] Add a concise marimo demo that constructs `mo.ui.anywidget(GridDraw(...))`, shows `grid.value["dots"]`, and shows `grid.value["lines"]`.
- [ ] Add reference markdown for `wigglystuff.grid_draw.GridDraw`.
- [ ] Add gallery rows/tiles to README and docs index.
- [ ] Add LLM context, API index, AGENTS quick reference, and Unreleased changelog entry.
- [ ] Add a small `.webp` gallery screenshot placeholder generated from a local drawing mockup.
- [ ] Run `uv run marimo check demos/griddraw.py`; expected pass.
- [ ] Run `uv run demos/griddraw.py`; expected pass.

### Task 4: Final Verification

**Files:**
- Verify all files touched in Tasks 1-3.

**Interfaces:**
- Consumes: complete GridDraw implementation.
- Produces: fresh evidence for completion.

- [ ] Run `uv run python -c "from wigglystuff import GridDraw; w=GridDraw(line_width=[1,2,4]); w.add_dot(2,3); w.add_line((0,0),(0,1), width=4); print(w.dots, w.lines); w.clear(); print(w.dots, w.lines)"`.
- [ ] Run `uv run pytest tests/test_grid_draw.py tests/test_imports.py -q`.
- [ ] Run `uv run marimo check demos/griddraw.py`.
- [ ] Run `uv run demos/griddraw.py`.
- [ ] Run `git diff -- package-lock.json` and confirm it is empty.
