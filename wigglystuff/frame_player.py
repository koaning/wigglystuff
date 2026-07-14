"""FramePlayer widget — play a sequence of images as a looping "video"."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List

import anywidget
import traitlets

from .chart_puck import fig_to_base64
from .paint import input_to_pil, pil_to_base64


def _encode_frame(frame: Any) -> str:
    """Convert a single frame to a base64 data URI.

    Accepts a matplotlib figure, PIL Image, file path, URL, bytes, or base64
    string. Matplotlib figures are detected by their ``savefig`` attribute so
    the (optional) dependency is never imported at module import time.
    """
    if hasattr(frame, "savefig"):
        return fig_to_base64(frame)
    return pil_to_base64(input_to_pil(frame))


class FramePlayer(anywidget.AnyWidget):
    """Play a sequence of images as an inline, optionally-looping "video".

    Hook up any iterable of frames — PIL images, file paths, URLs, bytes,
    base64 strings, or matplotlib figures (mixed is fine) — and the widget
    renders the current frame with play/pause/loop controls and a scrubber,
    so you don't need a second cell that reads a slider value and re-renders.

    For long or high-resolution sequences, downsize the frames before passing
    them in — every frame is base64-inlined into the widget model.

    Examples:
        ```python
        import marimo as mo
        from PIL import Image
        from wigglystuff import FramePlayer

        frames = [Image.new("RGB", (128, 128), (i * 8 % 255, 0, 0)) for i in range(30)]
        player = mo.ui.anywidget(FramePlayer(frames, interval_ms=80, loop=True))
        player
        ```
    """

    _esm = Path(__file__).parent / "static" / "frame-player.js"
    _css = Path(__file__).parent / "static" / "frame-player.css"

    frames = traitlets.List(traitlets.Unicode()).tag(sync=True)
    value = traitlets.Int(0).tag(sync=True)
    interval_ms = traitlets.Int(100).tag(sync=True)
    playing = traitlets.Bool(False).tag(sync=True)
    loop = traitlets.Bool(True).tag(sync=True)
    width = traitlets.Int(0).tag(sync=True)
    show_index = traitlets.Bool(True).tag(sync=True)

    def __init__(
        self,
        frames: Iterable[Any],
        value: int = 0,
        interval_ms: int = 100,
        loop: bool = True,
        width: int = 0,
        show_index: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a FramePlayer.

        Args:
            frames: Iterable of frame sources (PIL Image, path, URL, bytes,
                base64 string, or matplotlib figure). Must be non-empty.
            value: Starting frame index.
            interval_ms: Milliseconds between frames while playing.
            loop: Wrap back to the first frame at the end instead of stopping.
            width: Display width in pixels (0 = the image's natural width).
            show_index: Show the "current / total" frame readout.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        encoded = self._encode_frames(frames)
        if not encoded:
            raise ValueError("frames must contain at least one frame.")
        if interval_ms <= 0:
            raise ValueError("interval_ms must be positive.")
        value = max(0, min(value, len(encoded) - 1))
        super().__init__(
            frames=encoded,
            value=value,
            interval_ms=interval_ms,
            loop=loop,
            width=width,
            show_index=show_index,
            **kwargs,
        )

    @staticmethod
    def _encode_frames(frames: Iterable[Any]) -> List[str]:
        """Encode an iterable of frame sources into base64 data URIs."""
        return [_encode_frame(f) for f in frames]

    def set_frames(self, frames: Iterable[Any]) -> None:
        """Replace the frame sequence, re-encoding and clamping ``value``."""
        encoded = self._encode_frames(frames)
        if not encoded:
            raise ValueError("frames must contain at least one frame.")
        self.frames = encoded
        if self.value > len(encoded) - 1:
            self.value = len(encoded) - 1

    @property
    def n_frames(self) -> int:
        """Number of frames currently loaded."""
        return len(self.frames)
