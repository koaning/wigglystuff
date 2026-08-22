"""A draggable panel that floats any marimo content above the notebook."""

from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets

CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")


class _FloatDrag(anywidget.AnyWidget):
    """A content-less companion that makes the panel float and drag.

    It owns no content: the ESM climbs out of its shadow root to the
    ``[data-fp-root]`` container ``FloatingPanel`` laid out, builds the drag
    header there, promotes the root to ``position: fixed``, and wires drag and
    the minimize toggle. ``x``/``y`` hold the dragged viewport position (``-1``
    means "not yet dragged -- use ``corner``"); ``width`` of ``None`` shrink-wraps
    to content; ``collapsed`` hides the body, leaving just the draggable header.
    """

    _esm = Path(__file__).parent / "static" / "floating-panel.js"
    x = traitlets.Float(-1.0).tag(sync=True)
    y = traitlets.Float(-1.0).tag(sync=True)
    corner = traitlets.Unicode("bottom-right").tag(sync=True)
    width = traitlets.Int(allow_none=True, default_value=None).tag(sync=True)
    collapsed = traitlets.Bool(False).tag(sync=True)


def _require_marimo_notebook():
    """Raise unless we are displaying inside a running marimo notebook.

    ``FloatingPanel`` renders by reaching into marimo's rendered DOM, so it is a
    no-op anywhere else. Mirrors the check in ``wigglystuff/widget_dag.py``.
    """
    try:
        import marimo as mo

        if mo.running_in_notebook():
            return
    except ImportError:
        pass
    raise RuntimeError(
        "FloatingPanel is a marimo-only display helper: it renders by reaching "
        "into marimo's rendered DOM and does not work outside a running marimo "
        "notebook."
    )


class FloatingPanel:
    """Pin any marimo content in a draggable panel that floats above the page.

    Wraps ``child`` in a ``position: fixed`` panel that stays in view while the
    notebook scrolls, is draggable by its header, and can be minimized. Unlike
    ``Pip`` (which opens a separate Picture-in-Picture window), the panel is an
    ordinary element in the page, so it also works inside an iframe such as
    molab. This is a marimo-only display helper, not an ``AnyWidget``: display it
    as the last expression of a cell and keep reading ``.value`` off the widgets
    you passed in -- they stay fully live.

    A ``FloatingPanel`` renders as ordinary marimo content, so it composes: the
    ``child`` can be a single ``mo.ui`` element, an ``mo.vstack``/``mo.hstack``
    layout, a chart, an image, or a wigglystuff widget.

    Args:
        child: The content to float -- anything marimo can render.
        corner: Where the panel starts before it is dragged: ``"top-left"``,
            ``"top-right"``, ``"bottom-left"`` or ``"bottom-right"``.
        width: Panel width in pixels. Defaults to ``None``, which shrink-wraps
            the panel to its content -- the right choice for most content, since
            marimo widgets keep their own width. Set an integer for a fixed
            width, e.g. to reflow long text.
        collapsed: Start minimized, showing only the draggable header. The
            header's ``−``/``+`` toggle collapses and expands it; nothing is ever
            fully dismissed, so the content is always one click away.

    Example:
        ```python
        import marimo as mo
        from wigglystuff import FloatingPanel

        slider = mo.ui.slider(1, 10, label="N")
        FloatingPanel(slider, corner="top-right")
        ```
    """

    def __init__(
        self,
        child: Any,
        *,
        corner: str = "bottom-right",
        width: Optional[int] = None,
        collapsed: bool = False,
    ) -> None:
        if corner not in CORNERS:
            raise ValueError(f"corner must be one of {CORNERS}, got {corner!r}")
        if width is not None and width <= 0:
            raise ValueError(f"width must be positive, got {width}")
        self.child = child
        self.corner = corner
        self.width = width
        self.collapsed = collapsed
        self._html = None

    def _repr_mimebundle_(self, **kwargs):
        # marimo renders via ``_mime_``, so this only fires in Jupyter/IPython,
        # where it turns a silent plain-text repr into a clear error.
        _require_marimo_notebook()

    def _mime_(self):
        # marimo's ``as_html`` honours ``_mime_`` on any object, which is what
        # lets a FloatingPanel be the last expression of a cell -- and compose
        # inside other marimo content. Returning a raw HTML string (not an
        # ``mo.md`` object) is deliberate: interpolating live content into an
        # ``mo.md`` HTML block renders empty; ``Hint`` hits the same wall.
        _require_marimo_notebook()
        if self._html is None:
            self._html = self._build_html()
        return "text/html", self._html

    def _build_html(self):
        import marimo as mo

        # ``mo.Html`` rather than ``mo.md``: these wrappers are already HTML, so
        # there is no markdown to run. And always interpolate ``.text`` -- an
        # ``mo.md`` object formats itself back to its *markdown source*, which a
        # raw HTML block would leave unrendered.
        body = mo.Html(f"<div data-fp-body>{mo.as_html(self.child).text}</div>")
        # The companion promotes the root to ``position: fixed`` from JS; keep
        # the wrapper minimal here.
        overlay = mo.ui.anywidget(
            _FloatDrag(
                corner=self.corner, width=self.width, collapsed=self.collapsed
            )
        )
        return (
            f'<div data-fp-root style="position:relative">'
            f"{body.text}{overlay.text}</div>"
        )
