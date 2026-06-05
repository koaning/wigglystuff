# Excalidraw API

::: wigglystuff.excalidraw.Excalidraw

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `scene` | `dict` | Excalidraw scene (`elements` / `appState` / `files`). |
| `image_base64` | `str` | PNG data URL of the drawing; read via `get_pil()`. |
| `theme` | `str` | `"light"` (default) or `"dark"`; `""` follows the notebook theme. |
| `height` | `int` | Canvas height in pixels. |
| `sync_throttle_ms` | `int` | Minimum delay between syncing edits back to Python. |

Excalidraw itself is loaded from a CDN the first time the widget renders, so the
widget needs network access and does not work fully offline.
