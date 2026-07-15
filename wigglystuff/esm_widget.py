"""EsmWidget: render an inline ES module in the notebook with a data bridge."""

from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class EsmWidget(anywidget.AnyWidget):
    """Render an inline `ES module <https://developer.mozilla.org/docs/Web/JavaScript/Guide/Modules>`_ in a notebook.

    This is a thin, library-agnostic runner. You hand it a JavaScript ES module
    (the ``code``), and it loads that module in the browser and calls its
    ``render`` function. Because the module is loaded as a *real* ES module,
    top-level ``import`` statements work — so you can pull any library straight
    from a CDN (motion.dev, Observable Plot, d3, chart.js, three.js, …)::

        import { animate } from "https://cdn.jsdelivr.net/npm/motion@12/+esm";

    The module must follow the standard `anywidget
    <https://anywidget.dev/en/afm/>`_ contract — ``export default { render }`` —
    where ``render`` receives ``{ model, el }``, may append to ``el``, and may
    return a cleanup function.

    The point of the widget is the ``data`` traitlet: a JSON-able value synced
    both ways. Update it from Python and the browser sees a ``change:data``
    event; set it from JS and Python sees the new value. Crucially, changing
    ``data`` does **not** re-run ``render`` — your module observes the change and
    decides what to do, so animation libraries can *tween* toward the new state
    instead of hard-cutting.

    Examples:
        Tween on data change with motion.dev:

        ```python
        import marimo as mo
        from wigglystuff import EsmWidget

        w = EsmWidget(
            '''
            import { animate } from "https://cdn.jsdelivr.net/npm/motion@12/+esm";
            export default {
              render({ model, el }) {
                const box = document.createElement("div");
                box.style.cssText = "width:60px;height:60px;background:#e94560";
                el.appendChild(box);
                const draw = () => animate(box, { x: model.get("data").x }, { type: "spring" });
                draw();
                model.on("change:data", draw);
              }
            }
            ''',
            data={"x": 0},
            width=600,
            height=200,
        )
        mo.ui.anywidget(w)
        # ...then, from another cell:
        w.data = {"x": 240}   # the box springs to the new position
        ```

        Redraw on data change with Observable Plot:

        ```python
        EsmWidget(
            '''
            import * as Plot from "https://cdn.jsdelivr.net/npm/@observablehq/plot@0.6.17/+esm";
            export default {
              render({ model, el }) {
                const draw = () => el.replaceChildren(
                  Plot.plot({ marks: [Plot.dot(model.get("data").points, { x: "x", y: "y" })] })
                );
                draw();
                model.on("change:data", draw);
              }
            }
            ''',
            data={"points": [{"x": 1, "y": 2}, {"x": 2, "y": 1}]},
        )
        ```

        Point at a local file or a URL instead of an inline string:

        ```python
        EsmWidget("widgets/chart.js")
        EsmWidget("https://example.com/widget.js")
        ```

    The module is executed verbatim in the browser, so only pass JavaScript you
    trust (typically your own).
    """

    _esm = Path(__file__).parent / "static" / "esm-widget.js"
    _css = Path(__file__).parent / "static" / "esm-widget.css"

    code = traitlets.Unicode("").tag(sync=True)
    css = traitlets.Unicode("").tag(sync=True)
    data = traitlets.Any(None).tag(sync=True)
    width = traitlets.Int(500).tag(sync=True)
    height = traitlets.Int(300).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        code: Optional[str] = None,
        *,
        src: Optional[str] = None,
        data: Any = None,
        css: str = "",
        width: int = 500,
        height: int = 300,
        **kwargs: Any,
    ) -> None:
        """Create an EsmWidget.

        The module source is resolved in Python, so the browser always receives
        plain JavaScript. ``code`` (or ``src``) may be any of:

        * an inline JavaScript ES module string,
        * a path to a local ``.js`` file, or
        * an ``http(s)://`` URL.

        URLs and file paths are fetched/read here at construction time; the
        detection is by value, so ``EsmWidget("https://.../widget.js")`` and
        ``EsmWidget("export default { render() {} }")`` both do the right thing.

        Args:
            code: Inline ES module JavaScript, a local file path, or an
                ``http(s)://`` URL. Mutually exclusive with ``src``.
            src: An explicit alias for ``code`` (same accepted forms), handy
                when the intent is "load from here". Mutually exclusive with
                ``code``.
            data: Any JSON-able value, synced two-way with the browser. Defaults
                to ``{}``.
            css: Optional inline CSS injected into the widget root.
            width: Container width in pixels.
            height: Container height in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If neither or both of ``code`` and ``src`` are given.
        """
        if (code is None) == (src is None):
            raise ValueError("Provide exactly one of `code` or `src`.")

        source = code if code is not None else src
        super().__init__(
            code=self._resolve_source(source),
            css=css,
            data={} if data is None else data,
            width=width,
            height=height,
            **kwargs,
        )

    @staticmethod
    def _resolve_source(source: str) -> str:
        """Return module JS: fetch a URL, read a local file, or pass JS through."""
        text = str(source)
        if text.startswith("http://") or text.startswith("https://"):
            import urllib.request

            with urllib.request.urlopen(text) as response:
                return response.read().decode("utf-8")
        # A path to an existing file? Read it. Otherwise treat it as inline JS.
        # (Multi-line JS makes an invalid path, so is_file() is safely False.)
        try:
            path = Path(text)
            if path.is_file():
                return path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
        return text
