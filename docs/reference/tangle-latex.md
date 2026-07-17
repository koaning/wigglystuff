# TangleLatex API

::: wigglystuff.tangle_latex.TangleLatex

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `latex` | `str` | LaTeX source containing `\tangle{name}` markers. |
| `parameters` | `dict` | Per-parameter config (value, bounds, step, digits, color, symbol, ...). |
| `values` | `dict` | Live current value for each parameter; updates while dragging. |
| `display_mode` | `bool` | Render the formula in display mode. |
| `editor` | `str` | Exact-value editor style: `"popover"` or `"inline"`. |
| `reveal_all_on_drag` | `bool` | Reveal every tangle value while dragging any one of them. |
| `theme` | `str` | `"auto"`, `"light"`, or `"dark"`. |
| `error` | `str` | Validation/render error surfaced from the widget. |
