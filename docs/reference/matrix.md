---
title: "Matrix: editable numeric matrix widget"
description: Matrix is a spreadsheet-like editor for a grid of numbers in Jupyter, with value bounds, row and column labels, and optional diagonal mirroring.
image: matrix
image_alt: Matrix widget showing a 3 by 2 grid of editable decimal numbers inside bracket delimiters
---

# Matrix API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="matrix" data-demo-title="Matrix live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/matrix.webp" alt="Matrix widget showing a 3 by 2 grid of editable decimal numbers inside bracket delimiters" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`Matrix` is a spreadsheet-like editor for a grid of numbers, with `min_value` and
`max_value` bounds, `row_names`/`col_names` labels, and `mirror` to keep edits
symmetric across the diagonal. It is the quick way to hand-build a covariance
matrix, a transition table or a small weight grid and watch the result downstream.
If you are on marimo, prefer `marimo.ui.matrix`; this widget stays for plain Jupyter
and other anywidget hosts.

See also: [Slider2D](slider2d.md) for two coupled numbers instead of a grid,
[SortableList](sortable-list.md) for ordering items rather than editing values, and
[TangleSlider](tangle.md) for a single number inline in text.

::: wigglystuff.matrix.Matrix

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `matrix` | `list[list[float]]` | Cell values. |
| `rows` | `int` | Row count. |
| `cols` | `int` | Column count. |
| `min_value` | `float` | Minimum allowed value. |
| `max_value` | `float` | Maximum allowed value. |
| `mirror` | `bool` | Mirror edits across the diagonal when enabled. |
| `step` | `float` | Step size for edits. |
| `digits` | `int` | Decimal precision for display. |
| `row_names` | `list[str]` | Optional row labels. |
| `col_names` | `list[str]` | Optional column labels. |
| `static` | `bool` | Disable editing when true. |
| `flexible_cols` | `bool` | Allow column count changes interactively. |

