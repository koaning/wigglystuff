---
title: "FormulaAnimation: step through a LaTeX derivation"
description: FormulaAnimation animates a LaTeX derivation one line at a time from a list of tex/note steps, with prev/next buttons, opt-in arrow keys, and a reactive step trait you can drive from Python.
image: formulaanimation
image_alt: A quadratic-formula derivation with the current line centered, the previous line dimmed above it, and a caption underneath
---

# FormulaAnimation API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="formula_animation" data-demo-title="FormulaAnimation live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/formulaanimation.webp" alt="A quadratic-formula derivation with the current line centered, the previous line dimmed above it, and a caption underneath" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`FormulaAnimation` steps through a LaTeX derivation one line at a time. Give it a
list of `{"tex": ..., "note": ...}` dicts and the current line sits centered while
the previous line floats above it dimmed, with a short caption under the active
line. Playback is manual: move with the built-in prev/next buttons, with the arrow
keys (click the widget to opt into keyboard control), or by driving the reactive
`step` trait from Python — for example, an `mo.ui.slider` in another cell. With
`spotlight=True` a final step frames the finished formula alone in an elevated
card. The `steps` list is plain JSON, so an LLM can emit a derivation directly.

See also: [TangleLatex](tangle-latex.md) for a single formula with draggable
numbers, and [FramePlayer](frame-player.md) for stepping through a sequence of
rendered images.

::: wigglystuff.formula_animation.FormulaAnimation

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `steps` | `list[dict]` | Normalized `{"tex": str, "note": str}` derivation lines. |
| `title` | `str \| None` | Optional heading rendered above the animation. |
| `spotlight` | `bool` | Append a final step framing the last formula alone. |
| `step` | `int` | Current index; reactive, slider-drivable, moved by buttons/keys. |
| `height` | `int` | Height of the animation stage in pixels. |
| `theme` | `str` | `"auto"`, `"light"`, or `"dark"`. |
| `error` | `str` | Set if KaTeX fails to load in the browser. |
