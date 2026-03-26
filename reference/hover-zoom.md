# HoverZoom API


 Bases: `AnyWidget`


Image widget with a magnified side panel that appears on hover.


Hovering over the image shows a rectangle indicator and a zoom panel to the right displaying the magnified region — the classic e-commerce product zoom pattern.



```
from wigglystuff import HoverZoom

from wigglystuff import HoverZoom

# From a file path
widget = HoverZoom("photo.jpg", zoom_factor=3.0)

# From a matplotlib figure
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.scatter(x, y, s=5, alpha=0.5)
widget = HoverZoom(fig, zoom_factor=4.0)
```


Create a HoverZoom widget.


  Source code in `wigglystuff/hover_zoom.py`

```
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
```


## get_pil_zoom


```
get_pil_zoom()
```


Return the currently zoomed region as a PIL Image.


Returns the cropped portion of the image that is visible in the zoom panel. Returns `None` if no image is set.

 Source code in `wigglystuff/hover_zoom.py`

```
def get_pil_zoom(self):
    """Return the currently zoomed region as a PIL Image.

    Returns the cropped portion of the image that is visible in the
    zoom panel. Returns ``None`` if no image is set.
    """
    if not self.image:
        return None
    img = base64_to_pil(self.image)
    x0_r, y0_r, x1_r, y1_r = self._crop
    w, h = img.size
    return img.crop((int(x0_r * w), int(y0_r * h), int(x1_r * w), int(y1_r * h)))
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `image` | `str` | Base64-encoded image data. |
| `zoom_factor` | `float` | Magnification level for the zoom panel. |
| `width` | `int` | Display width of the source image in pixels. |
| `height` | `int` | Display height in pixels (0 = auto). |
