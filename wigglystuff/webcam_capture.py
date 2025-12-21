"""Webcam capture widget with manual and interval snapshots."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

import anywidget
import traitlets


class WebcamCapture(anywidget.AnyWidget):
    """Webcam capture widget with manual and interval snapshots.

    The widget shows a live webcam preview plus a capture button and an
    auto-capture toggle. When ``capturing`` is enabled, the browser updates
    ``image_base64`` on the cadence specified by ``interval_ms``.

    Examples:
        ```python
        cam = WebcamCapture(interval_ms=1000)
        cam
        ```
    """

    _esm = Path(__file__).parent / "static" / "webcam-capture.js"
    _css = Path(__file__).parent / "static" / "webcam-capture.css"

    image_base64 = traitlets.Unicode("").tag(sync=True)
    capturing = traitlets.Bool(False).tag(sync=True)
    interval_ms = traitlets.Int(1000).tag(sync=True)
    facing_mode = traitlets.Unicode("user").tag(sync=True)
    ready = traitlets.Bool(False).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(self, interval_ms: int = 1000, facing_mode: str = "user") -> None:
        """Create a WebcamCapture widget.

        Args:
            interval_ms: Capture interval in milliseconds when auto-capture is on.
            facing_mode: Camera facing mode ("user" or "environment").
        """
        super().__init__(interval_ms=interval_ms, facing_mode=facing_mode)

    def get_bytes(self) -> bytes:
        """Return the captured frame as raw bytes."""
        if not self.image_base64:
            return b""
        payload = self.image_base64
        if "base64," in payload:
            payload = payload.split("base64,", 1)[1]
        return base64.b64decode(payload)

    def get_pil(self):
        """Return the captured frame as a PIL Image."""
        if not self.image_base64:
            return None
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ImportError("PIL is required to use get_pil().") from exc

        return Image.open(BytesIO(self.get_bytes()))
