# ApiDoc API


 Bases: `AnyWidget`


Renders API documentation for a Python class or function in a notebook.



```
from wigglystuff import ApiDoc

from wigglystuff import ApiDoc

ApiDoc(MyClass)
```


Create an ApiDoc widget.


  Source code in `wigglystuff/api_doc.py`

```
def __init__(self, obj: Any = None, *, width: int = 700, show_private: bool = False):
    """Create an ApiDoc widget.

    Args:
        obj: A Python class or function to document.
        width: Maximum pixel width for the widget.
        show_private: Whether to include _-prefixed methods.
    """
    self._obj = obj
    super().__init__(width=width, show_private=show_private)
    if obj is not None:
        self.doc = _extract_doc(obj, show_private)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `doc` | `dict` | Introspected documentation payload (auto-generated from the target object). |
| `width` | `int` | Container width in pixels. |
| `show_private` | `bool` | Whether to include private (underscore-prefixed) methods. |
