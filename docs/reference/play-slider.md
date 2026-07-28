---
title: "PlaySlider: animated slider with play button"
description: PlaySlider adds a play/pause button to a slider so it auto-advances on a timer, turning any index-parameterized computation into an animation.
image: playslider
image_alt: PlaySlider with a pause button and a value of 43 driving an animated sine plot below it
---

# PlaySlider API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="play_slider" data-demo-title="PlaySlider live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/playslider.webp" alt="PlaySlider with a pause button and a value of 43 driving an animated sine plot below it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`PlaySlider` is a slider with a play/pause button that walks `value` from
`min_value` to `max_value` by itself, one `step` every `interval_ms`, optionally
looping back to the start. Reach for it when a computation is already parameterized
by an index — frames, epochs, timesteps — and you want to watch it move instead of
dragging the handle yourself.

See also: [FramePlayer](frame-player.md) for playing back a sequence of images,
[HoverSlider](hover-slider.md) for previewing a value before committing to it, and
[CircularSlider](circular-slider.md) for a dial-shaped range.

::: wigglystuff.play_slider.PlaySlider

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `int` | Current slider value. |
| `min_value` | `int` | Minimum value. |
| `max_value` | `int` | Maximum value. |
| `step` | `int` | Step size per tick. |
| `interval_ms` | `int` | Milliseconds between auto-advance ticks. |
| `playing` | `bool` | Whether the slider is currently auto-advancing. |
| `loop` | `bool` | Whether to loop back to `min_value` after reaching `max_value`. |
| `width` | `int` | Widget width in pixels. |
