"""An arrow and a note pointing at a live widget."""

from pathlib import Path

import anywidget
import traitlets

SIDES = ("left", "right", "top", "bottom")


class _Arc(anywidget.AnyWidget):
    """A pure SVG overlay that curves from the note box to the target box.

    It owns no content: the ESM climbs out of its shadow root to the
    ``[data-hint-root]`` container ``Hint`` laid out and draws the arc into it,
    so the SVG shares a coordinate space with the two ``[data-hint-box]`` boxes.
    """

    _esm = Path(__file__).parent / "static" / "hint.js"
    side = traitlets.Unicode("right").tag(sync=True)
    color = traitlets.Unicode("currentColor").tag(sync=True)


def _require_marimo_notebook():
    """Raise unless we are displaying inside a running marimo notebook.

    ``Hint`` renders by reaching into marimo's rendered DOM, so it is a no-op
    anywhere else. Mirrors the check in ``wigglystuff/widget_dag.py``.
    """
    try:
        import marimo as mo

        if mo.running_in_notebook():
            return
    except ImportError:
        pass
    raise RuntimeError(
        "Hint is a marimo-only display helper: it renders by reaching into "
        "marimo's rendered DOM and does not work outside a running marimo "
        "notebook."
    )


class Hint:
    """Point an arrow at a widget and explain it, right in the notebook.

    Wraps ``target`` and draws a curved arrow from ``note`` to the edge of the
    target's box, so a reader knows what to interact with and why. This is a
    marimo-only display helper, not an ``AnyWidget``: display it as the last
    expression of a cell and keep reading ``.value`` off the widget you passed in.

    A ``Hint`` renders as ordinary marimo content, so it composes: put several in
    an ``mo.hstack``, drop one into an ``mo.md`` f-string, or nest one inside
    another to hang two arrows off the same widget.

    Args:
        target: The widget being annotated -- anything marimo can render.
        note: The explanation. A ``str`` is rendered with ``mo.md`` (so markdown
            and LaTeX work); any other object is rendered as-is.
        side: Where the note sits: ``"left"``, ``"right"``, ``"top"`` or
            ``"bottom"``.
        color: Any CSS color, applied to the arc and its arrowhead. Defaults to
            ``"currentColor"``, so the arc picks up the notebook's own text
            color and follows a light/dark theme switch for free.
        gap: Space between the two boxes, in marimo stack-gap units. The arc
            needs somewhere to live, so a little room helps.

    Example:
        ```python
        import marimo as mo
        from wigglystuff import Hint

        slider = mo.ui.slider(1, 10, label="N")
        Hint(slider, "drag to change **N**")
        ```
    """

    def __init__(self, target, note, *, side="right", color="currentColor", gap=3):
        if side not in SIDES:
            raise ValueError(f"side must be one of {SIDES}, got {side!r}")
        self.target = target
        self.note = note
        self.side = side
        self.color = color
        self.gap = gap
        self._html = None

    def _repr_mimebundle_(self, **kwargs):
        # marimo renders via ``_mime_``, so this only fires in Jupyter/IPython,
        # where it turns a silent plain-text repr into a clear error.
        _require_marimo_notebook()

    def _mime_(self):
        # marimo's ``as_html`` honours ``_mime_`` on any object, so implementing
        # it is what makes a Hint composable: it can go in an mo.hstack, an
        # mo.md f-string, or inside another Hint. Subclassing ``mo.Html`` would
        # do the same, but marimo is not a wigglystuff dependency and a
        # module-level base class would need it at import time.
        _require_marimo_notebook()
        if self._html is None:
            self._html = self._build_html()
        return "text/html", self._html

    def _build_html(self):
        import marimo as mo

        note = mo.md(self.note) if isinstance(self.note, str) else self.note
        # ``mo.Html`` rather than ``mo.md``: these wrappers are already HTML, so
        # there is no markdown to run. And always interpolate ``.text`` -- an
        # ``mo.md`` object formats itself back to its *markdown source*, which a
        # raw HTML block like the div below would leave unrendered.
        target_box = mo.Html(
            f'<div data-hint-box="target" style="display:inline-block">'
            f"{mo.as_html(self.target).text}</div>"
        )
        note_box = mo.Html(
            f'<div data-hint-box="note" style="display:inline-block">'
            f"{mo.as_html(note).text}</div>"
        )
        # The note trails the target on the right/bottom and leads it otherwise.
        boxes = [target_box, note_box]
        if self.side in ("left", "top"):
            boxes.reverse()
        if self.side in ("left", "right"):
            board = mo.hstack(boxes, gap=self.gap, align="center", justify="start")
        else:
            board = mo.vstack(boxes, gap=self.gap, align="center")
        overlay = mo.ui.anywidget(_Arc(side=self.side, color=self.color))
        return (
            f'<div data-hint-root style="position:relative;display:inline-block">'
            f"{board.text}{overlay.text}</div>"
        )
