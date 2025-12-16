"""Paint widget ported from the mopaint project."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Union
import urllib.request

import anywidget
import traitlets

DEFAULT_HEIGHT = 500
DEFAULT_WIDTH = 889


def base64_to_pil(base64_string: str):
    """Convert a base64 string to a PIL Image."""
    from PIL import Image

    if "base64," in base64_string:
        base64_string = base64_string.split("base64,")[1]

    img_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(img_data))


def pil_to_base64(img):
    """Convert a PIL Image to a base64 data URL string."""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def create_empty_image(width: int = 500, height: int = 500, background_color=(255, 255, 255, 255)):
    """Create an empty image with given dimensions and background color."""
    from PIL import Image

    return Image.new("RGBA", (width, height), background_color)


def input_to_pil(input_data: Union[str, Path, "Image.Image", bytes, None]):
    """Convert an input object (path, bytes, URL, etc.) into a PIL Image."""
    from PIL import Image

    if input_data is None:
        return None

    if hasattr(input_data, "mode") and hasattr(input_data, "size"):
        return input_data

    if isinstance(input_data, (str, Path)):
        input_str = str(input_data)

        if input_str.startswith(("http://", "https://")):
            with urllib.request.urlopen(input_str, timeout=10) as response:
                img_data = response.read()
            return Image.open(BytesIO(img_data))

        if "base64," in input_str or (
            len(input_str) > 50
            and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in input_str.replace("\n", "").replace("\r", ""))
        ):
            return base64_to_pil(input_str)

        file_path = Path(input_str)
        if not file_path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        return Image.open(file_path)

    if isinstance(input_data, bytes):
        return Image.open(BytesIO(input_data))

    raise ValueError(
        f"Unsupported input type: {type(input_data)}. Expected PIL Image, file path, URL, base64 string, or bytes."
    )


class Paint(anywidget.AnyWidget):
    """Notebook-friendly paint widget with MS Paint style tools and PIL helpers.

    Examples:
        ```python
        paint = Paint(width=400, height=300)
        paint
        ```
    """

    _esm = Path(__file__).parent / "static" / "paint.js"
    _css = Path(__file__).parent / "static" / "paint.css"

    base64 = traitlets.Unicode("").tag(sync=True)
    height = traitlets.Int(DEFAULT_HEIGHT).tag(sync=True)
    width = traitlets.Int(DEFAULT_WIDTH).tag(sync=True)  # rough 16:9 ratio
    store_background = traitlets.Bool(True).tag(sync=True)

    def __init__(self, height: int = DEFAULT_HEIGHT, width: int = DEFAULT_WIDTH, store_background: bool = True, init_image: Optional[Any] = None):
        """Create a Paint widget.

        Args:
            height: Canvas height in pixels.
            width: Canvas width in pixels (ignored when ``init_image`` sets aspect ratio).
            store_background: Persist previous strokes when background changes.
            init_image: Optional path/URL/PIL image/bytes to preload.
        """
        super().__init__()

        user_provided_width = width != DEFAULT_WIDTH
        user_provided_height = height != DEFAULT_HEIGHT

        if init_image is not None and user_provided_width:
            raise ValueError(
                "Cannot specify both init_image and explicit width parameter. "
                "Canvas width is automatically calculated from the image aspect ratio."
            )

        if init_image is not None:
            pil_image = input_to_pil(init_image)
            if pil_image is not None:
                image_width, image_height = pil_image.size
                aspect_ratio = image_width / image_height

                if user_provided_height:
                    self.height = height
                    self.width = int(height * aspect_ratio)
                else:
                    self.width = image_width
                    self.height = image_height

                encoded = pil_to_base64(pil_image).split(",")[1]
                self.base64 = encoded
            else:
                self.width = width
                self.height = height
                self.base64 = ""
        else:
            self.width = width
            self.height = height
            self.base64 = ""

        self.store_background = store_background

    def get_pil(self):
        """Return the current drawing as a PIL Image."""
        if not self.base64:
            return create_empty_image(width=self.width, height=self.height, background_color=(0, 0, 0, 0))

        return base64_to_pil(self.base64)

    def get_base64(self) -> str:
        """Return the current drawing as a base64 string (data URL)."""
        if not self.base64:
            return ""
        return pil_to_base64(self.get_pil())
