---
title: "TangleSlider: inline draggable number input"
description: TangleSlider, TangleChoice and TangleSelect drop draggable numbers and inline option pickers into Jupyter or marimo prose, Bret Victor style.
image: tangle
image_alt: Tangle sliders as draggable underlined percentages inside a sentence, driving a line chart below
---

# Tangle Widgets API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="tangle" data-demo-title="Tangle live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/tangle.webp" alt="Tangle sliders as draggable underlined percentages inside a sentence, driving a line chart below" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

The Tangle widgets put a control inside your prose rather than next to it, after
Bret Victor's Tangle. `TangleSlider` renders a number you drag left and right,
`TangleChoice` cycles through labels in place when you click it, and `TangleSelect`
is the same choice as a dropdown. Interpolate one into a markdown string and the
sentence itself becomes the interface.

See also: [TangleLatex](tangle-latex.md) for draggable numbers inside a KaTeX
formula, [HoverSlider](hover-slider.md) for a conventional track that also reports
what the pointer is over, and [SortableList](sortable-list.md) for reordering a set
of options instead of picking one.

## TangleSlider

::: wigglystuff.tangle.TangleSlider

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `amount` | `float` | Current value. |
| `min_value` | `float` | Lower bound. |
| `max_value` | `float` | Upper bound. |
| `step` | `float` | Step size. |
| `pixels_per_step` | `int` | Drag distance per step. |
| `prefix` | `str` | Text before the value. |
| `suffix` | `str` | Text after the value. |
| `digits` | `int` | Decimal precision for display. |


## TangleChoice

::: wigglystuff.tangle.TangleChoice

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |


## TangleSelect

::: wigglystuff.tangle.TangleSelect

### Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |

