---
title: "TangleLatex: draggable LaTeX formula numbers"
description: TangleLatex renders a KaTeX formula whose numbers you drag inside the equation itself, syncing every value back to Python from Jupyter or Colab.
image: tanglelatex
image_alt: A rendered quadratic formula with its three coefficients shown as colored, underlined draggable numbers
---

# TangleLatex API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="tangle_latex" data-demo-title="TangleLatex live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/tanglelatex.webp" alt="A rendered quadratic formula with its three coefficients shown as colored, underlined draggable numbers" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`TangleLatex` renders a KaTeX formula in which named numbers are draggable. Mark
them with `\tangle{name}` inside `latex` and configure each name in `parameters`; a
parameter can show its formatted number or stay symbolic until it is dragged or
edited, and repeated markers share one value. The live numbers land in `values`
while you drag, so downstream cells recompute as the equation changes.

See also: [Tangle widgets](tangle.md) for the same drag gesture in plain prose,
[Matrix](matrix.md) for editing numbers as a grid, and
[Slider2D](slider2d.md) for two coupled parameters on one canvas.

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
