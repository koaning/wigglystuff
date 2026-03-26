# Paint API


 Bases: `AnyWidget`


Notebook-friendly drawing canvas with brush, marker, eraser, undo, and PIL helpers.



```
from wigglystuff import Paint

from wigglystuff import Paint

paint = Paint(width=400, height=300)
paint
```


Create a Paint widget.


  Source code in `wigglystuff/paint.py`

```
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

    if init_image is not None:
        pil_image = input_to_pil(init_image)
        if pil_image is not None:
            image_width, image_height = pil_image.size
            aspect_ratio = image_width / image_height

            if user_provided_width and user_provided_height:
                self.width = width
                self.height = height
                if abs(width / height - aspect_ratio) > 0.01:
                    warnings.warn(
                        f"Specified dimensions ({width}x{height}) have a different aspect ratio "
                        f"than the image ({image_width}x{image_height}). Image will be scaled to fit."
                    )
            elif user_provided_width:
                self.width = width
                self.height = int(width / aspect_ratio)
            elif user_provided_height:
                self.height = height
                self.width = int(height * aspect_ratio)
            else:
                self.width = image_width
                self.height = image_height

            if (self.width, self.height) != pil_image.size:
                from PIL import Image as _PILImage
                pil_image = pil_image.resize(
                    (self.width, self.height), _PILImage.LANCZOS
                )
            encoded = pil_to_base64(pil_image).split(",")[1]
            self.base64 = encoded
        else:
            self.width = width
            self.height = height
            self.base64 = pil_to_base64(
                create_empty_image(width, height, (0, 0, 0, 0))
            ).split(",")[1]
    else:
        self.width = width
        self.height = height
        self.base64 = pil_to_base64(
            create_empty_image(width, height, (0, 0, 0, 0))
        ).split(",")[1]

    self.store_background = store_background
```


## get_base64


```
get_base64() -> str
```


Return the current drawing as a base64 string (data URL).

 Source code in `wigglystuff/paint.py`

```
def get_base64(self) -> str:
    """Return the current drawing as a base64 string (data URL)."""
    if not self.base64:
        return ""
    return pil_to_base64(self.get_pil())
```


## get_pil


```
get_pil()
```


Return the current drawing as a PIL Image.

 Source code in `wigglystuff/paint.py`

```
def get_pil(self):
    """Return the current drawing as a PIL Image."""
    if not self.base64:
        return create_empty_image(width=self.width, height=self.height, background_color=(0, 0, 0, 0))

    return base64_to_pil(self.base64)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `base64` | `str` | PNG data URL or raw base64 payload. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |
| `store_background` | `bool` | Persist strokes when background changes. |
