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


## to_markdown


```
to_markdown() -> str
```


Export the API documentation as a Markdown string.

 Source code in `wigglystuff/api_doc.py`

```
def to_markdown(self) -> str:
    """Export the API documentation as a Markdown string."""
    doc = self.doc
    if not doc or not doc.get("name"):
        return ""

    parts = []

    # Title
    prefix = f"{doc['module']}." if doc.get("module") else ""
    parts.append(f"## `{prefix}{doc['name']}`")
    parts.append(f"\n> {doc.get('kind', 'class')}")

    # Signature
    if doc.get("signature"):
        parts.append(f"\n```python\n{doc['name']}{doc['signature']}\n```")

    # Bases
    if doc.get("bases"):
        bases = ", ".join(f"`{b}`" for b in doc["bases"])
        parts.append(f"\nBases: {bases}")

    # Docstring
    if doc.get("docstring"):
        parts.append(f"\n{doc['docstring']}")

    # Parameter table
    params = doc.get("parameters", [])
    if params:
        parts.append("\n| Name | Type | Default |")
        parts.append("| --- | --- | --- |")
        for p in params:
            name = f"`{p['name']}`"
            ann = f"`{p['annotation']}`" if p.get("annotation") else ""
            default = f"`{p['default']}`" if p.get("default") else ""
            parts.append(f"| {name} | {ann} | {default} |")

    # Methods
    methods = doc.get("methods", [])
    if methods:
        parts.append("\n### Methods")
        for m in methods:
            sig = m.get("signature", "()")
            decorator = f" *{m['decorator']}*" if m.get("decorator") else ""
            parts.append(f"\n#### `{m['name']}{sig}`{decorator}")
            if m.get("docstring"):
                parts.append(f"\n{m['docstring']}")

    # Properties
    props = doc.get("properties", [])
    if props:
        parts.append("\n### Properties")
        for p in props:
            parts.append(f"\n#### `{p['name']}` *property*")
            if p.get("docstring"):
                parts.append(f"\n{p['docstring']}")

    return "\n".join(parts)
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `doc` | `dict` | Introspected documentation payload (auto-generated from the target object). |
| `width` | `int` | Container width in pixels. |
| `show_private` | `bool` | Whether to include private (underscore-prefixed) methods. |
