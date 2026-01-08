# CopyToClipboard API


 Bases: `AnyWidget`


Button widget that copies the provided `text_to_copy` payload.



```
from wigglystuff import CopyToClipboard

button = CopyToClipboard(text_to_copy="Hello, world!")
button
```


Create a CopyToClipboard button.


  Source code in `wigglystuff/copy_to_clipboard.py`

```
def __init__(self, text_to_copy: str = "", **kwargs: Any):
    """Create a CopyToClipboard button.

    Args:
        text_to_copy: Initial string placed on the clipboard when clicked.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    super().__init__(**kwargs)
    self.text_to_copy = text_to_copy
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `text_to_copy` | `str` | Payload copied when the button is pressed. |
