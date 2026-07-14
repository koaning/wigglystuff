# FramePlayer API

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
