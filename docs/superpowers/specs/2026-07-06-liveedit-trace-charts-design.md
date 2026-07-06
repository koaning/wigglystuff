# LiveEdit Trace Charts — Design Spec

## Problem

When tracing loops with `LiveEdit`, users can see per-pass values in a table
but cannot easily visualise how variables change across iterations. Spotting
convergence, oscillation, or trends requires mentally scanning many rows of
repr strings.

## Goal

Let users select numeric column(s) in a loop's trace table and see an
overlaid line chart — iteration on X, variable value on Y — rendered inline
inside the widget. No re-tracing, no separate widget, no Python-roundtrip.

## Design

### Numeric detection (Python side)

A new `numerics` dictionary is added to each serialized loop node in the
trace. During collection, after each assignment the value is attempted via
`float(value)` inside a try/except. The float or `None` is stored alongside
the repr string in a `_numerics` dict on the pass record. During
`_serialize_loop`, each column is checked: if every pass has a non-None
float, the column appears in the `numerics` output dict.

```python
# added inside _serialize_loop, alongside columns/passes
"numerics": {
  "low":  [0, 3, 3, 4, 4],
  "mid":  [2, 2, 3, 3, 4],
  "high": [5, 5, 5, 5, 5],
}
```

The `numerics` dict is built in `_serialize_loop` after all passes are
assembled. For each column, if every pass has a stored numeric value (not
None), it is included; otherwise the column is omitted.

Only columns where **every pass** has a valid float are included. If a column
appears in `numerics`, its header is clickable.

### Column header click interaction (JS)

- Numeric column headers (`<th>` elements) get `cursor: pointer` and a subtle
  chart icon (SVG inline or unicode `📈`) visible on hover.
- Click toggles selection: clicking a non-selected header adds it to the
  loop's selected set; clicking a selected header removes it.
- Zero selected = no chart rendered.
- When a loop has selected columns, the loop block switches to a flexbox row
  layout: `<table> | <chart-panel>`.

### Chart rendering (JS)

A lightweight SVG line chart is rendered in vanilla JS (no D3 dependency):

- **Canvas size:** 280 × 180 px, inside a `<div class="liveedit-chart">`.
- **Margins:** 10 px top, 10 px right, 20 px bottom (for X labels), 40 px left
  (for Y labels).
- **Axes:** `<path>` for X and Y baselines, tick marks at 4–6 intervals.
- **Lines:** One `<path>` per selected column. Stroke color from a fixed
  palette (blue, orange, green, red, purple, teal, pink).
- **Y scale:** Auto-scaled from min/max across all selected columns, with
  ~5 % padding.
- **X scale:** Linear 0 to (n_passes - 1).
- **Data points:** Small circles on each line at each pass.
- **Tooltip:** Hovering near a data point shows a floating label with the
  exact value.

### Close/clear mechanism

- Clicking a selected column header again deselects it (toggle).
- A small "×" button in the top-right corner of the chart panel clears all
  selections and hides the chart.
- When the last selected column is deselected, the chart panel disappears.

### Layout

Per-loop block structure (before):

```
<div class="liveedit-loopblock">
  <div class="liveedit-badgerow"> ... </div>
  <table class="liveedit-table"> ... </table>
</div>
```

Per-loop block structure (with chart):

```
<div class="liveedit-loopblock liveedit-loopblock-charting">
  <div class="liveedit-badgerow"> ... </div>
  <div class="liveedit-loopbody">
    <table class="liveedit-table"> ... </table>
    <div class="liveedit-chart">
      <button class="liveedit-chart-close">×</button>
      <svg ...> ... </svg>
    </div>
  </div>
</div>
```

`.liveedit-loopbody` uses `display: flex; flex-direction: row; gap: 12px`.

### Theming

Chart colors, axis lines, and text follow existing CSS variables. New CSS
custom properties on `.liveedit-root`:

- `--liveedit-chart-line-0`, `--liveedit-chart-line-1`, etc. (stroke palette)
- `--liveedit-chart-bg`: background of chart panel
- `--liveedit-chart-axis`: stroke color for axes/grid

### No Python API changes

- `LiveEdit` class unchanged — no new traitlets, no new methods.
- `_Collector` gains numeric recording but the change is internal only.
- `trace` dict gains the `numerics` key on loop nodes; existing keys
  (`columns`, `passes`) unchanged for backward compat.

## Files changed

| File | Change |
|---|---|
| `wigglystuff/live_edit.py` | `_Collector` stores float-parsed values; `_serialize_loop` emits `numerics` dict |
| `wigglystuff/static/liveedit.js` | Column click toggles, SVG chart renderer, loop-block flex layout |
| `wigglystuff/static/liveedit.css` | Chart panel styles, selected-column indicator, chart icon |

## Non-goals

- Editing or removing data points from within the chart.
- Pan/zoom of chart.
- Exporting chart as image.
- Nested loop charting (out of scope for v1 — nested loop data is sparser and
  harder to lay out).
