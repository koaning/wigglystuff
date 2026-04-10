"""ApiDoc widget for rendering Python class/function documentation in notebooks."""

import inspect
from pathlib import Path
from typing import Any

import anywidget
import traitlets


def _format_annotation(ann):
    """Best-effort conversion of a type annotation to a readable string."""
    if ann is inspect.Parameter.empty:
        return ""
    if isinstance(ann, type):
        return ann.__qualname__
    return str(ann)


def _extract_params(sig):
    """Extract parameter info from an inspect.Signature."""
    params = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        entry = {"name": name}
        entry["annotation"] = _format_annotation(param.annotation)
        if param.default is not inspect.Parameter.empty:
            entry["default"] = repr(param.default)
        else:
            entry["default"] = ""
        kind = param.kind
        if kind == inspect.Parameter.VAR_POSITIONAL:
            entry["name"] = f"*{name}"
        elif kind == inspect.Parameter.VAR_KEYWORD:
            entry["name"] = f"**{name}"
        elif kind == inspect.Parameter.KEYWORD_ONLY:
            entry["keyword_only"] = True
        params.append(entry)
    return params


def _extract_methods(cls, show_private):
    """Extract methods from a class, skipping object builtins."""
    methods = []
    object_attrs = set(dir(object))
    for name in sorted(dir(cls)):
        if name in object_attrs:
            continue
        if name.startswith("__") and name.endswith("__"):
            continue
        if name.startswith("_") and not show_private:
            continue
        try:
            attr = getattr(cls, name)
        except Exception:
            continue
        if not callable(attr) and not isinstance(attr, (classmethod, staticmethod)):
            continue
        # Skip properties
        if isinstance(inspect.getattr_static(cls, name, None), property):
            continue
        entry = {"name": name, "docstring": inspect.getdoc(attr) or ""}
        # Detect classmethod/staticmethod
        raw = inspect.getattr_static(cls, name, None)
        if isinstance(raw, classmethod):
            entry["decorator"] = "classmethod"
        elif isinstance(raw, staticmethod):
            entry["decorator"] = "staticmethod"
        try:
            sig = inspect.signature(attr)
            entry["signature"] = str(sig)
            entry["parameters"] = _extract_params(sig)
        except (ValueError, TypeError):
            entry["signature"] = "(...)"
            entry["parameters"] = []
        methods.append(entry)
    return methods


def _extract_properties(cls):
    """Extract property descriptors from a class."""
    props = []
    for name in sorted(dir(cls)):
        raw = inspect.getattr_static(cls, name, None)
        if isinstance(raw, property):
            props.append({
                "name": name,
                "docstring": inspect.getdoc(raw) or "",
            })
    return props


def _extract_doc(obj, show_private=False):
    """Main entry point: extract documentation structure from a class or function."""
    if isinstance(obj, type):
        return _extract_class_doc(obj, show_private)
    elif inspect.isfunction(obj) or inspect.isbuiltin(obj) or inspect.ismethod(obj):
        return _extract_function_doc(obj)
    else:
        # Callable instances, plain objects — document their class
        return _extract_class_doc(type(obj), show_private)


def _extract_class_doc(cls, show_private):
    """Extract documentation structure from a class."""
    module = cls.__module__
    if module == "__main__":
        module = ""
    doc = {
        "kind": "class",
        "name": cls.__name__,
        "module": module,
        "docstring": inspect.getdoc(cls) or "",
        "bases": [b.__name__ for b in cls.__bases__ if b is not object],
    }
    try:
        sig = inspect.signature(cls)
        doc["signature"] = str(sig)
        doc["parameters"] = _extract_params(sig)
    except (ValueError, TypeError):
        doc["signature"] = "(...)"
        doc["parameters"] = []
    doc["methods"] = _extract_methods(cls, show_private)
    doc["properties"] = _extract_properties(cls)
    return doc


def _extract_function_doc(func):
    """Extract documentation structure from a function."""
    module = getattr(func, "__module__", "")
    if module == "__main__":
        module = ""
    doc = {
        "kind": "function",
        "name": func.__name__,
        "module": module,
        "docstring": inspect.getdoc(func) or "",
    }
    try:
        sig = inspect.signature(func)
        doc["signature"] = str(sig)
        doc["parameters"] = _extract_params(sig)
    except (ValueError, TypeError):
        doc["signature"] = "(...)"
        doc["parameters"] = []
    return doc


class ApiDoc(anywidget.AnyWidget):
    """Renders API documentation for a Python class or function in a notebook.

    Examples:
        ```python
        from wigglystuff import ApiDoc

        ApiDoc(MyClass)
        ```
    """

    _esm = Path(__file__).parent / "static" / "api-doc.js"
    _css = Path(__file__).parent / "static" / "api-doc.css"

    doc = traitlets.Dict(default_value={}).tag(sync=True)
    width = traitlets.Int(default_value=700).tag(sync=True)
    show_private = traitlets.Bool(default_value=False).tag(sync=True)

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

    @traitlets.observe("show_private")
    def _reextract(self, change):
        if getattr(self, "_obj", None) is not None:
            self.doc = _extract_doc(self._obj, change["new"])
