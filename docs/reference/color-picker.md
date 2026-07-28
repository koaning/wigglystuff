---
title: "ColorPicker: hex color input widget"
description: ColorPicker puts a native color input in a Jupyter or marimo cell and syncs the chosen hex string back to Python, with an rgb property for the channels.
image: colorpicker
image_alt: ColorPicker widget with a swatch and the browser color dialog open on blue, showing R, G and B values
---

# ColorPicker API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="colorpicker" data-demo-title="ColorPicker live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/colorpicker.webp" alt="ColorPicker widget with a swatch and the browser color dialog open on blue, showing R, G and B values" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`ColorPicker` wraps the browser's native color input and syncs the chosen `#RRGGBB`
value back to Python as `color`, with an `rgb` property that hands you the three channels
as integers. Reach for it when a plot color, a brush color or a mask tint is easier to
choose by eye than to type as a literal; `show_label` controls whether the hex string is
printed next to the swatch.

See also: [Paint](paint.md) for a canvas with the same picker built into its toolbar,
[CopyToClipboard](copy-to-clipboard.md) for handing the resulting hex string to someone
else, and [TangleSlider](tangle.md) for the same by-eye approach to numbers.

::: wigglystuff.color_picker.ColorPicker

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `color` | `str` | Hex color string (e.g., `#ff00aa`). |

