# Paint API


 Bases: `AnyWidget`


Notebook-friendly paint widget with MS Paint style tools and PIL helpers.


Examples:


```
paint = Paint(width=400, height=300)
paint
```


Create a Paint widget.


Parameters:


| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `height` | `int` | Canvas height in pixels. | `DEFAULT_HEIGHT` |
| `width` | `int` | Canvas width in pixels (ignored when `init_image` sets aspect ratio). | `DEFAULT_WIDTH` |
| `store_background` | `bool` | Persist previous strokes when background changes. | `True` |
| `init_image` | `Optional[Any]` | Optional path/URL/PIL image/bytes to preload. | `None` |

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
