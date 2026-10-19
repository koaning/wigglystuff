---
title: "StateViewer: animate the state inside a Python function"
description: StateViewer runs a Python function once, records every line it executes (recursion included), and plays it back in marimo next to a picture of the state that you draw yourself, such as an N-Queens board during backtracking search.
---

# StateViewer API

`StateViewer(search_func, view_func)` runs `search_func` once and records every
line it executes, including recursive calls. Calls into other functions are not
recorded. At each step it calls `view_func` with the function's local variables
and plays the whole run back:

- **left**: whatever `view_func` drew for that step;
- **right**: the source with the line about to run highlighted, plus a fixed
  table of every variable the function assigns (values that just changed
  flash, ones not assigned yet show *not assigned*);
- **bottom**: play/pause/step controls, a speed slider, the current call depth,
  and a timeline of the call depth over the whole run. Click or drag it to
  scrub, or use ← / → (Shift jumps 10) and Space when the widget has focus.

```python
from wigglystuff import StateViewer

def solve(board, row, n):
    if row == n:
        return True
    for col in range(n):
        if all(c != col and abs(c - col) != row - r for r, c in enumerate(board)):
            board.append(col)
            if solve(board, row + 1, n):
                return True
            board.pop()
    return False

def view(board, n, row=None, col=None):
    return draw_board_svg(board, n, candidate=(row, col))

StateViewer(solve, view, args=([], 0, 8))
```

`view_func`'s **parameter names pick the locals it receives**: `def view(board, n)`
gets the live `board` and `n`. Parameters with a default are optional. While a
required one isn't assigned yet, the previous view stays up. Each view is
rendered straight away, so in-place changes such as `board.append(col)` show up
correctly.

`view_func` can return anything marimo can display: an HTML/SVG string,
`mo.Html`/`mo.md`, a dataframe, even a matplotlib figure. Every distinct view is
stored in the widget, so small SVG strings are the best choice for long runs.
`max_steps` (default 20,000) stops recording a runaway search and sets
`truncated`, and `only_changes=True` keeps only the steps where the view changes.

From Python, `viewer.steps` holds the full trace: one record per step with
`line`, `depth`, `event` (`"line"`, `"return"` or `"raise"`), and the `locals`
as reprs. `viewer.step` follows the widget whenever you pause or scrub, and
`viewer.current` is the record at that step.

See also: [LiveEdit](live-edit.md) for a table of every loop iteration of one
run, and [AsyncFlow](async-flow.md) for async tasks.

::: wigglystuff.state_viewer.StateViewer

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `code` | `str` | Source of `search_func` (decorators dropped). |
| `lines` | `list[dict]` | Syntax tokens per source line, for highlighting. |
| `steps` | `list[dict]` | One record per step: `line`, `depth`, `event`, `view`, `locals` (plus `returned` on return steps). |
| `views` | `list[str]` | Deduplicated rendered HTML; `steps[i]["view"]` indexes into it (`-1` = nothing drawn yet). |
| `variables` | `list[str]` | Every local the run assigns, in definition order. |
| `step` | `int` | Current step; synced back when you pause or scrub, and settable from Python. |
| `playing` | `bool` | Whether playback is running. |
| `interval_ms` | `int` | Milliseconds per step while playing. |
| `loop` | `bool` | Restart from the first step at the end. |
| `returned` | `str \| None` | Repr of the return value. |
| `error` | `dict \| None` | `{type, message, source, lineno}` when `search_func` or `view_func` raised. |
| `truncated` | `bool` | Whether `max_steps` was reached. |
| `height` | `int` | Height cap in pixels (`0` = fit content). |
