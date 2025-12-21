# WebcamCapture API

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `image_base64` | `str` | PNG data URL for the latest frame. |
| `capturing` | `bool` | Enable auto-capture mode. |
| `interval_ms` | `int` | Auto-capture interval in milliseconds. |
| `facing_mode` | `str` | Camera facing mode ("user" or "environment"). |
| `ready` | `bool` | True when the preview stream is ready. |
| `error` | `str` | Error message when webcam access fails. |

::: wigglystuff.webcam_capture.WebcamCapture
