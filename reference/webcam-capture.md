# WebcamCapture API


 Bases: `AnyWidget`


Webcam capture widget with manual and interval snapshots.


The widget shows a live webcam preview plus a capture button and an auto-capture toggle. When `capturing` is enabled, the browser updates `image_base64` on the cadence specified by `interval_ms`.



```
from wigglystuff import WebcamCapture

cam = WebcamCapture(interval_ms=1000)
cam
```


Create a WebcamCapture widget.


  Source code in `wigglystuff/webcam_capture.py`

```
def __init__(self, interval_ms: int = 1000, facing_mode: str = "user") -> None:
    """Create a WebcamCapture widget.

    Args:
        interval_ms: Capture interval in milliseconds when auto-capture is on.
        facing_mode: Camera facing mode ("user" or "environment").
    """
    super().__init__(interval_ms=interval_ms, facing_mode=facing_mode)
```


## get_bytes


```
get_bytes() -> bytes
```


Return the captured frame as raw bytes.

 Source code in `wigglystuff/webcam_capture.py`

```
def get_bytes(self) -> bytes:
    """Return the captured frame as raw bytes."""
    if not self.image_base64:
        return b""
    payload = self.image_base64
    if "base64," in payload:
        payload = payload.split("base64,", 1)[1]
    return base64.b64decode(payload)
```


## get_pil


```
get_pil()
```


Return the captured frame as a PIL Image.

 Source code in `wigglystuff/webcam_capture.py`

```
def get_pil(self):
    """Return the captured frame as a PIL Image."""
    if not self.image_base64:
        return None
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("PIL is required to use get_pil().") from exc

    return Image.open(BytesIO(self.get_bytes()))
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `image_base64` | `str` | PNG data URL for the latest frame. |
| `capturing` | `bool` | Enable auto-capture mode. |
| `interval_ms` | `int` | Auto-capture interval in milliseconds. |
| `facing_mode` | `str` | Camera facing mode ("user" or "environment"). |
| `ready` | `bool` | True when the preview stream is ready. |
| `error` | `str` | Error message when webcam access fails. |
