# GridDraw — a drawable square grid widget

**Status:** Design approved (pending written-spec review)
**Date:** 2026-07-06

## Summary

`GridDraw` is a new wigglystuff AnyWidget that gives the user a square grid to
draw on, like a student with graph paper. Two things can be drawn:

- **Dots** sit on grid **intersections**.
- **Lines** sit on grid **segments** — the edges between two *orthogonally
  adjacent* intersections (horizontal and vertical only; no diagonals).

Dots and lines are two independent layers on the same canvas. Neither requires
the other. Python reads both back as plain data, so a program can treat what the
user drew as structured input (which intersections are marked, which segments
connect them).

This is a marimo-first widget: it is consumed via `mo.ui.anywidget(w)` and read
through `.value`, not via `.observe`.

Colors are explicitly **out of scope for v1** (see Deferred). Hex grids are a
possible future extension and are also out of scope.

## Goals

- A clean square grid the user can draw dots and lines on.
- Fast, forgiving interaction: click to place one item, drag to paint a run.
- An eraser and undo, because drawing tools need them.
- Light/dark theming that follows the notebook by default.
- A small Python API to pre-populate and read back the drawing.
- Sensible zero-config defaults; optional configuration only appears when asked
  for (e.g. a line-width picker).

## Non-goals (v1)

- Per-element or palette **colors** (deferred; the data model leaves room).
- **Diagonal** segments.
- **Hex** grids.
- Redo (undo only).
- Any Python-side graph/adjacency helpers. The read-back data is enough; callers
  derive whatever they need. (The user prefers not to frame this as a graph.)

## Interaction model (frontend)

Three modes, chosen from a toolbar:

| Mode | Click | Drag |
| --- | --- | --- |
| **Dot** | toggle a dot at the nearest intersection | paint dots across the intersections passed |
| **Line** | toggle the segment under the cursor | paint a run of segments along the path (axis-aligned) |
| **Eraser** | remove the dot/segment under the cursor | remove every dot/segment passed over |

Additional toolbar controls:

- **Undo** — button, plus `Cmd/Ctrl+Z`. Each completed gesture is one step: a
  single click, one drag stroke, or a Clear. Implemented as a snapshot stack
  (snapshot the full drawing before each gesture; undo restores the previous
  snapshot). Dumb and obvious on purpose; no redo.
- **Clear** — wipes the drawing (undoable).
- **Theme toggle** — flips light/dark locally.
- **Line-width picker** — only shown when `line_width` is a list (see below).

### Rendering order

Grid lines → faint placeholder dots (empty intersections) → drawn lines → drawn
dots. Placeholder dots render *under* the lines so a line cleanly covers the gray
dots at the intersections it crosses; only real drawn dots sit on top of lines.

### Theming

The widget root carries theme state and defines component CSS variables
(`--gd-bg`, `--gd-grid`, `--gd-ink`, etc.), marks `color-scheme: light dark`, and
provides `.dark` / `[data-theme="dark"]` overrides — the standard wigglystuff
pattern so notebook-level theme toggles work instantly. The **default drawing
ink is theme-aware**: near-black on light, near-white on dark, so a drawing is
always visible without the user choosing a color.

## Python API

```python
import marimo as mo
from wigglystuff import GridDraw

w = GridDraw(
    rows=8, cols=8,        # number of CELLS; intersections are (rows+1) x (cols+1)
    line_width=2,          # int → fixed width, no picker.
                           # list e.g. [1, 2, 4] → width picker; first is default.
    dot_radius=6,          # fixed dot size (px)
    theme=None,            # None → follow notebook; "light"/"dark" → force
    width=440, height=440, # widget pixel size
)

# Pre-populate from Python
w.add_dot(2, 3)
w.add_line((0, 0), (0, 1))          # endpoints must be orthogonally adjacent
w.add_line((0, 0), (0, 1), width=4) # optional per-line width

grid = mo.ui.anywidget(w)
grid
```

```python
# ── a reactive cell ──
grid.value["dots"]    # [[row, col], ...]
grid.value["lines"]   # [{"from": [r, c], "to": [r, c], "width": int}, ...]
```

### Constructor arguments

| Arg | Type | Default | Notes |
| --- | --- | --- | --- |
| `rows` | int | `8` | number of cells vertically; row indices `0..rows` |
| `cols` | int | `8` | number of cells horizontally; col indices `0..cols` |
| `line_width` | int \| list[int] | `2` | int = fixed, no UI; list = width picker (first = default) |
| `dot_radius` | int | `6` | fixed dot size in px |
| `theme` | str \| None | `None` | `None` follows notebook; `"light"`/`"dark"` force |
| `width` | int | `440` | widget pixel width |
| `height` | int | `440` | widget pixel height |

**Naming note:** `width`/`height` are the widget's pixel size (consistent with
every other wigglystuff widget), and `line_width` is stroke thickness. The names
are distinct enough that we keep both rather than renaming pixel size to `size`.

### Synced traitlets

| Traitlet | Type | Direction | Shape |
| --- | --- | --- | --- |
| `dots` | List | both | `[[row, col], ...]` |
| `lines` | List | both | `[{"from": [r,c], "to": [r,c], "width": int}, ...]` |
| `rows`, `cols` | Int | Python → JS | grid size |
| `line_width` | Int or List | Python → JS | drives width picker |
| `dot_radius` | Int | Python → JS | dot size |
| `theme` | Unicode/None | both | initial + toggle state |
| `width`, `height` | Int | Python → JS | pixel size |

### Helper methods

- `add_dot(row, col)` — add a dot at an intersection. Validates bounds. Idempotent
  (adding an existing dot is a no-op).
- `add_line(a, b, width=None)` — add a segment between two adjacent intersections
  `a=(r,c)`, `b=(r,c)`. Validates bounds and orthogonal adjacency; raises
  `ValueError` otherwise. `width` defaults to the default line width.
- `clear()` — remove all dots and lines.

All three mutate the synced traitlets so the frontend updates live.

### Validation

- `rows`, `cols`, `dot_radius`, `width`, `height`: positive ints.
- `line_width`: a positive int, or a non-empty list of positive ints.
- `add_dot` / `add_line`: indices within `0..rows` / `0..cols`.
- `add_line`: endpoints exactly one step apart orthogonally (`|dr| + |dc| == 1`).

## Data model rationale

- **Intersections vs cells.** `rows`/`cols` count cells; intersections are the
  `(rows+1) x (cols+1)` grid corners. Coordinates are `[row, col]` integers with
  `[0, 0]` at the top-left corner.
- **A "line" is one unit segment** between adjacent intersections. This keeps the
  stored data clean and adjacency-friendly regardless of how it was drawn. The
  *painting* interaction (drag a run) is decoupled from the *storage* (a set of
  unit segments): a drag simply adds each unit segment along its path.
- **Segments are canonicalized** (endpoints sorted) so the same segment can't be
  stored twice with different endpoint order.
- **Undo/eraser are frontend-only.** They mutate `dots`/`lines`, which sync back;
  Python needs no special API for them.

## File layout (follows existing wigglystuff widgets)

- `wigglystuff/grid_draw.py` — `GridDraw(AnyWidget)`; `_esm`/`_css` point to
  `static/griddraw.js` / `static/griddraw.css`.
- `js/grid-draw/widget.js` — source (vanilla JS + SVG, in the style of
  `edge_draw` / `spline_draw`). Built to `wigglystuff/static/griddraw.js` via an
  esbuild script in `package.json`.
- `wigglystuff/static/griddraw.css` — theme variables + light/dark.
- `wigglystuff/__init__.py` — import `GridDraw`, add to `__all__`.
- `demos/griddraw.py` — a marimo demo notebook.

## Testing

- **Python smoke tests / unit tests:** construct with defaults; `add_dot` /
  `add_line` update traitlets; `add_line` rejects non-adjacent and
  out-of-bounds endpoints; `line_width` accepts int and list, rejects bad input;
  `clear()` empties both layers.
- **Manual notebook verification** (required for widget UI, per repo practice):
  draw dots/lines by click and drag; eraser; undo + `Cmd/Ctrl+Z`; theme toggle
  and default-ink visibility in dark; line-width picker appears only for a list;
  `grid.value` reflects the drawing in a reactive marimo cell.

## Docs / release chores (per CLAUDE.md)

Update `docs/index.md`, `readme.md`, `docs/llms.txt`, `CHANGELOG.md`
(`## [Unreleased]`), the CLAUDE.md/agents.md quick-reference table, add a
`.webp` gallery screenshot, and give the demo a MoLab link carrying
`?utm_source=wigglystuff`.

## Deferred (future work)

- **Colors:** `colors=[...]` palette → swatch picker; per-dot/per-line `color`
  added to the traitlet dicts; theme-aware default when omitted. The data model
  already leaves room (dots can grow from `[r,c]` to a dict; lines already carry
  a dict).
- **Hex grids.**
- **Diagonal segments.**
- **Redo.**
- **Per-dot size picker** (`dot_radius` as a list), mirroring `line_width`.
