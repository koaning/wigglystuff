"""HoverZoom widget — magnified side panel on image hover."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

import anywidget
import traitlets

from .chart_puck import fig_to_base64
from .paint import base64_to_pil, input_to_pil, pil_to_base64


class HoverZoom(anywidget.AnyWidget):
    """Image widget with a magnified side panel that appears on hover.

    Hovering over the image shows a rectangle indicator and a zoom panel
    to the right displaying the magnified region — the classic e-commerce
    product zoom pattern.

    Examples:
        ```python
        from wigglystuff import HoverZoom

        # From a file path
        widget = HoverZoom("photo.jpg", zoom_factor=3.0)

        # From a matplotlib figure
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.scatter(x, y, s=5, alpha=0.5)
        widget = HoverZoom(fig, zoom_factor=4.0)
        ```
    """

    _esm = Path(__file__).parent / "static" / "hover-zoom.js"
    _css = Path(__file__).parent / "static" / "hover-zoom.css"

    image = traitlets.Unicode("").tag(sync=True)
    zoom_factor = traitlets.Float(3.0).tag(sync=True)
    width = traitlets.Int(500).tag(sync=True)
    height = traitlets.Int(0).tag(sync=True)

    def __init__(
        self,
        image: Optional[Union[str, Path, Any]] = None,
        *,
        zoom_factor: float = 3.0,
        width: int = 500,
        height: int = 0,
    ):
        """Create a HoverZoom widget.

        Args:
            image: Image source — matplotlib figure, file path, URL, PIL Image,
                bytes, or base64 string.
            zoom_factor: Magnification level for the zoom panel.
            width: Display width of the source image in pixels.
            height: Display height in pixels (0 = auto, preserve aspect ratio).
        """
        super().__init__()
        self.zoom_factor = zoom_factor
        self.width = width
        self.height = height

        if image is not None:
            # Detect matplotlib figures by checking for savefig
            if hasattr(image, "savefig"):
                self.image = fig_to_base64(image)
            else:
                pil_image = input_to_pil(image)
                if pil_image is not None:
                    self.image = pil_to_base64(pil_image)

    def get_pil(self):
        """Return the current image as a PIL Image."""
        if not self.image:
            return None
        return base64_to_pil(self.image)
