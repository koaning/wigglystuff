---
title: "FramePlayer: play image frames as video"
description: FramePlayer turns a list of PIL images, file paths, URLs or matplotlib figures into an inline looping video with play, pause and scrub controls in marimo.
image: frameplayer
image_alt: FramePlayer showing a matplotlib sine wave frame with a play button and scrubber below it
---

# FramePlayer API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="frame_player" data-demo-title="FramePlayer live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/frameplayer.webp" alt="FramePlayer showing a matplotlib sine wave frame with a play button and scrubber below it" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`FramePlayer` takes any iterable of frames — PIL images, file paths, URLs, bytes, base64
strings or matplotlib figures, mixed is fine — and plays them inline with play/pause, loop
and a scrubber, which saves writing a second cell that reads a slider and re-renders. Use
`set_frames()` to swap the sequence later and `n_frames` to check how many are loaded.
Every frame is base64-inlined into the widget model, so downsize long or high-resolution
sequences before passing them in.

See also: [PlaySlider](play-slider.md) if you would rather drive your own render step,
[ImageRefreshWidget](image-refresh.md) for one image slot updated live as it is computed,
and [WebcamCapture](webcam-capture.md) for collecting the frames in the first place.

::: wigglystuff.frame_player.FramePlayer

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `frames` | `list[str]` | Base64 data URIs, one per frame. |
| `value` | `int` | Index of the currently displayed frame. |
| `interval_ms` | `int` | Milliseconds between frames while playing. |
| `playing` | `bool` | Whether playback is currently running. |
| `loop` | `bool` | Wrap back to the first frame at the end instead of stopping. |
| `width` | `int` | Display width in pixels (`0` = the image's natural width). |
| `show_index` | `bool` | Whether to show the "current / total" frame readout. |
