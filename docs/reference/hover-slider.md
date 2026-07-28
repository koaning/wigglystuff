---
title: "HoverSlider: slider with live hover preview"
description: HoverSlider reports the value under your pointer alongside the value you clicked, so a marimo cell can preview a result before you commit to it.
image: hover_slider
image_alt: HoverSlider in a notebook cell showing a committed value of 0.10 and a hovered value of 0.30 below the track
---

# HoverSlider API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="hover_slider" data-demo-title="HoverSlider live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/hover_slider.webp" alt="HoverSlider in a notebook cell showing a committed value of 0.10 and a hovered value of 0.30 below the track" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`HoverSlider` treats hovering as an input channel of its own: `hover_value` follows
the pointer while `value` stays parked where you last clicked, so a cell can show
you what a setting would do before you commit to it. Pass `start`/`stop`/`step` for
a linear range or `steps` for a list of discrete values, and use
`sync_throttle_ms` to cap how often the hover stream reruns downstream cells.

See also: [PlaySlider](play-slider.md) for stepping through a range on a timer,
[CircularSlider](circular-slider.md) for the same range laid out on a dial, and
[TangleSlider](tangle.md) for a draggable number that lives inside a sentence.

::: wigglystuff.hover_slider.HoverSlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int \| float` | Committed value. Moves on click, drag, and arrow keys — never on plain hover. |
| `hover_value` | `int \| float` | Value under the pointer. Falls back to `value` when the pointer leaves, so it is never `None`. |
| `hovering` | `bool` | Whether the pointer is on the track, i.e. whether `hover_value` is live. |
| `start` | `int \| float` | Lower bound. In `steps` mode this is `steps[0]`. |
| `stop` | `int \| float` | Upper bound. In `steps` mode this is `steps[-1]`. |
| `step` | `int \| float \| None` | Snap increment. `None` in `steps` mode. |
| `steps` | `list[int \| float]` | Discrete values, laid out evenly across the track. Empty means linear mode. |
| `sync_throttle_ms` | `int` | Cap on how often hover updates reach Python. `0` syncs every pointer move. |
| `show_value` | `bool` | Render the committed and hovered values below the track. |
| `label` | `str` | Text above the track. Empty string hides it. |
| `color` | `str` | CSS color for the fill, puck border, and hover marker. Empty uses the theme default. |
| `width` | `int` | Widget width in pixels. |
