---
title: "CircularSlider: circular dial slider widget"
description: CircularSlider and CircularRangeSlider lay a value range around a dial you drag, including spans that wrap past the seam, in marimo or Jupyter.
image: circle-slider
image_alt: Two circular dial sliders side by side, one showing a single value of 42 and one showing a range
---

# CircularSlider API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="circular_slider" data-demo-title="CircularSlider live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/circle-slider.webp" alt="Two circular dial sliders side by side, one showing a single value of 42 and one showing a range" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`CircularSlider` lays a value range around a dial: `start` sits at 12 o'clock and
values increase clockwise. `CircularRangeSlider` is the two-handle version, and
because the track is a circle a drag across the seam gives you a wrap-around
`(low, high)` tuple where `low > high` — which is what you want for hours, angles
and compass headings. Both mirror `mo.ui.slider` and `mo.ui.range_slider`
semantics, so `start`, `stop`, `step` and `value` behave as you already expect.

See also: [HoverSlider](hover-slider.md) for a linear track that also reports the
value under the pointer, [PlaySlider](play-slider.md) for a slider that advances on
a timer, and [Slider2D](slider2d.md) for steering two parameters with one gesture.

::: wigglystuff.circular_slider.CircularSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `float` | Current value, mapped onto the circular track. |
| `start` | `float` | Lower bound of the value range (sits at 12 o'clock). |
| `stop` | `float` | Upper bound of the value range. |
| `step` | `float` | Snap increment in value units. |
| `size` | `int` | Diameter in pixels. |
| `thickness` | `int` | Ring track thickness in pixels. |
| `show_value` | `bool` | Render the current value as text below the dial. |
| `color` | `str` | CSS color for the fill arc and handle border (e.g. `"#ef4444"`). Empty string follows the light/dark theme. |
| `label` | `str` | Optional text label shown above the dial. Empty string hides it. |

---

::: wigglystuff.circular_slider.CircularRangeSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `tuple[float, float]` | Current `(low, high)` range. A drag that crosses the 12 o'clock seam produces a wrap-around tuple where `low > high`. |
| `start` | `float` | Lower bound of the value range. |
| `stop` | `float` | Upper bound of the value range. |
| `step` | `float` | Snap increment in value units. |
| `size` | `int` | Diameter in pixels. |
| `thickness` | `int` | Ring track thickness in pixels. |
| `show_value` | `bool` | Render the current `low – high` range as text below the dial. |
