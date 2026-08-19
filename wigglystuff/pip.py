"""A wrapper that floats another widget in a picture-in-picture window."""

from pathlib import Path
from typing import Any

import anywidget
import traitlets

_ESM_PATH = Path(__file__).parent / "static" / "pip.js"
_CSS_PATH = Path(__file__).parent / "static" / "pip.css"


class Pip(anywidget.AnyWidget):
    """A wrapper that floats another widget in a picture-in-picture window.

    A `Pip` draws the widget it wraps inline, with a button in the top-right
    corner. Pressing that button moves the widget into a window that floats
    above other windows, including other applications, and leaves a placeholder
    in the notebook that brings it back.

    The wrapped widget is the same object in both places. Its traits, observers
    and value are unaffected by where it is drawn, so a `Pip` can be dropped
    around an existing widget without changing any code that reads it.

    Only a click can open the window; the browser refuses to open one on a
    program's request. Closing it can be done from either side: by the reader,
    or by setting `floating` to `False`.

    Warning:
        This is the browser's [Document Picture-in-Picture](https://developer.mozilla.org/en-US/docs/Web/API/Document_Picture-in-Picture_API)
        window, and it inherits two limits from that API.

        The first is availability. Chromium and Firefox implement it; Safari does
        not, and there the button is not drawn and the child stays inline. A tab
        is allowed one such window, so opening a second `Pip` closes the first,
        which restores its inline view. And the request must come from a
        top-level page, so a notebook inside an iframe cannot open one.

        The second is that the window is a document of its own, with its own
        `window` and `document`, separate from the notebook's. A widget that
        listens on the notebook's `window` — as most drag handling does, to
        follow the pointer outside the element — never receives the events that
        happen while it floats, and stops responding to dragging until it comes
        back. Widgets that use pointer capture on their own element work in both
        places. Styles reach the window along the same lines: the child's own
        stylesheet is mounted into it, and the notebook's light or dark setting
        is mirrored so the two match, but the notebook's own classes and
        variables are not, so a widget drawn with those looks unstyled there.

    Args:
        child: The widget to wrap. Any widget with a `model_id` works.
        width: Width of the floating window in pixels, when first opened.
        height: Height of the floating window in pixels, when first opened.

    Attributes:
        floating: Whether the child is in the floating window. Setting this to
            `False` closes the window. Setting it to `True` has no effect and
            reports a warning to the browser console.

    Raises:
        traitlets.TraitError: If `child` is not a widget.
        ValueError: If `width` or `height` is not positive.

    Examples:
        A grid that can be drawn on while it floats beside another window:

        ```python
        import marimo as mo
        from wigglystuff import GridDraw, Pip

        sketch = GridDraw(rows=6, cols=6, width=300, height=300)
        Pip(sketch, width=340, height=360)
        ```

        The wrapped widget is read the same way in either place:

        ```python
        sketch.dots
        ```

        In marimo, wrap the child in `mo.ui.anywidget` when cells that read it
        should re-run as it changes, and reach the widget through `.widget`:

        ```python
        sketch = mo.ui.anywidget(GridDraw(rows=6, cols=6))
        panel = mo.ui.anywidget(Pip(sketch, width=340, height=360))
        panel
        ```

        ```python
        sketch.widget.dots  # this cell re-runs as the grid is drawn on
        ```

        Closing the window from Python:

        ```python
        panel.widget.floating = False
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    child = anywidget.WidgetTrait().tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(300).tag(sync=True)
    floating = traitlets.Bool(False).tag(sync=True)

    def __init__(
        self,
        child: Any,
        *,
        width: int = 400,
        height: int = 300,
        **kwargs: Any,
    ) -> None:
        super().__init__(child=child, width=width, height=height, **kwargs)

    @traitlets.validate("width", "height")
    def _validate_size(self, proposal: dict) -> int:
        value = proposal["value"]
        if value <= 0:
            raise ValueError(f"{proposal['trait'].name} must be positive, got {value}")
        return value
