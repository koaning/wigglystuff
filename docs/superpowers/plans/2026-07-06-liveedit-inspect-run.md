# LiveEdit Inspect Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `LiveEdit.inspect_run(fn, *args, **kwargs)` as a read-only AnyWidget that traces one Python function body and renders loop variable evolution top-to-bottom.

**Architecture:** Keep the backend as a `code -> trace + annotations + error` pipeline so a future live editor can update only the `code` traitlet and reuse the same retrace path. Split the Python work into source extraction, AST instrumentation/runner, pure trace building, and widget traitlet wiring. Keep the frontend renderer data-driven from `trace` and `annotations`, using the approved mockup as the behavior and styling reference.

**Tech Stack:** Python 3.10+, `anywidget`, `traitlets`, standard-library `ast`/`inspect`/`textwrap`; browser JavaScript/CSS bundled as static widget assets.

## Global Constraints

- Work only inside `/Users/vincentwarmerdam/Development/wigglystuff/.conductor/riga-v1`.
- Do not read or write `/Users/vincentwarmerdam/Development/wigglystuff`.
- No hard imports of optional dependencies such as numpy or pillow.
- Preserve `code -> trace -> annotations` for future editable live updates.
- The HTML mockup in `docs/superpowers/specs/2026-07-06-liveedit-inspect-run-mockup.html` is the visual and interaction source of truth.
- Do not modify `package-lock.json` unless intentionally updating JS dependencies.
- Use `origin/main` for diff comparisons.

---

### Task 1: Python Tracing Core

**Files:**
- Create: `wigglystuff/live_edit.py`
- Create: `tests/test_live_edit.py`

**Interfaces:**
- Produces: `LiveEdit(code, args=(), kwargs=None, editable=False, **kw)`, `LiveEdit.inspect_run(fn, *args, **kwargs)`, `inspect_run(fn, *args, **kwargs)`, and pure helpers `_trace_code(code, args, kwargs, function_name=None)`.
- Produces trace payload keys: `setup`, `body`, `returned`.
- Produces error payload keys: `type`, `message`, optional `lineno`.

- [ ] Write failing tests for binary search, nested loops, clear untraceable errors, and optional numpy repr snapshots.
- [ ] Run `uv run pytest tests/test_live_edit.py -q` and confirm the failures are for missing `LiveEdit` behavior.
- [ ] Implement source extraction, AST instrumentation, runner/collector, trace building, and widget construction.
- [ ] Run `uv run pytest tests/test_live_edit.py -q` until green.
- [ ] Smoke-test construction with `uv run python -c "from wigglystuff import LiveEdit; ..."` after the export exists.

### Task 2: Frontend Renderer

**Files:**
- Create: `wigglystuff/static/liveedit.js`
- Create: `wigglystuff/static/liveedit.css`
- Modify: `wigglystuff/live_edit.py`

**Interfaces:**
- Consumes: synced `code`, `trace`, `annotations`, `error`, `editable`, `theme`, `width`, `height`.
- Produces: read-only code and trace panels with delegated hover selection.

- [ ] Render setup rows, sequential loop blocks, nested loop subtables, and return chip from data only.
- [ ] Implement delegated hover resolution equivalent to the mockup: variable hover lights names/assign lines/columns/return, loop hover lights code bodies and all loop table instances, cell hover lights both.
- [ ] Add light/dark CSS variables scoped to the widget root and keep the value-cell readability behavior from the mockup.
- [ ] Smoke-test a widget instance so AnyWidget can load the static assets.

### Task 3: Package Integration, Demo, and Docs

**Files:**
- Modify: `wigglystuff/__init__.py`
- Create: `demos/liveedit.py`
- Create: `docs/reference/live-edit.md`
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/llms.txt`
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `LiveEdit` and `inspect_run` from `wigglystuff.live_edit`.
- Produces: package-root exports and a marimo demo.

- [ ] Re-export `LiveEdit` and `inspect_run` from package root.
- [ ] Add `LiveEdit` to the agent tables and gallery docs; ensure every MoLab link has `?utm_source=wigglystuff`.
- [ ] Add an Unreleased changelog entry.
- [ ] Run `uv run marimo check demos/liveedit.py`.
- [ ] Run `uv run demos/liveedit.py`.
- [ ] Run focused pytest and import smoke tests before completion.

