# Paint API

::: wigglystuff.paint.Paint

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `base64` | `str` | PNG data URL or raw base64 payload. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `store_background` | `bool` | Persist strokes when background changes. |
| `rainbow_brush` | `bool` | Show the rainbow spray tool (default off). |
| `brush` | `bool` | Show the thin brush tool. |
| `marker` | `bool` | Show the thick marker tool. |
| `eraser` | `bool` | Show the eraser tool. |
| `color_picker` | `bool` | Show the color picker. |
| `color` | `str` | Drawing color (hex); two-way synced with the picker. |

