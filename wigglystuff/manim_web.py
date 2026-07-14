"""ManimWeb widget for embedding manim-web animations in the notebook."""

from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


class ManimWeb(anywidget.AnyWidget):
    """Run a `manim-web <https://github.com/maloyan/manim-web>`_ scene in a notebook.

    ``manim-web`` is a TypeScript/WebGL reimplementation of Manim that renders
    animations entirely in the browser. This widget is a thin runner: it loads
    the manim-web engine from a CDN, then executes a blob of JavaScript you
    supply (the ``code`` traitlet). The animation plays inline; Python's only
    job is to hand over the source and the sizing.

    Your JavaScript is run as the body of an async function with the manim-web
    module namespace (``manim``), the target DOM element (``container``), the
    ``width`` / ``height`` ints, and the widget ``model`` in scope. The
    recommended entry point is manim-web's own ``Player``, which renders a full
    playback UI into ``container`` — play/pause, a scrub timeline with segment
    markers, speed control, fullscreen and export::

        const player = new manim.Player(container, {
            width, height, autoPlay: true, backgroundColor: manim.WHITE,
        });
        player.sequence(async (scene) => {
            const circle = new manim.Circle({
                radius: 1.5, color: manim.BLUE, fillOpacity: 1,
            });
            await scene.play(new manim.Create(circle));
        });

    ``PlayerOptions`` extends ``SceneOptions``, so ``width``/``height``/
    ``backgroundColor`` work alongside ``autoPlay`` and ``loop``. Colours are
    plain hex strings (``manim.BLUE``, or ``"#e94560"`` directly); set
    ``fillOpacity: 1`` for solid shapes on a light background.

    The code is executed verbatim in the browser, so only pass JavaScript you
    trust (typically your own).

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import ManimWeb

        scene = '''
            const player = new manim.Player(container, {
                width, height, autoPlay: true, backgroundColor: manim.WHITE,
            });
            player.sequence(async (scene) => {
                const c = new manim.Circle({
                    radius: 1.5, color: manim.BLUE, fillOpacity: 1,
                });
                await scene.play(new manim.Create(c));
            });
        '''
        mo.ui.anywidget(ManimWeb(code=scene, width=800, height=450))
        ```

        Point at a local file or a URL instead of an inline string — the first
        argument accepts any of the three forms:

        ```python
        ManimWeb("scenes/intro.js")
        ManimWeb("https://example.com/scene.js")
        ```
    """

    _esm = Path(__file__).parent / "static" / "manim-web.js"
    _css = Path(__file__).parent / "static" / "manim-web.css"

    code = traitlets.Unicode("").tag(sync=True)
    width = traitlets.Int(500).tag(sync=True)
    height = traitlets.Int(300).tag(sync=True)
    version = traitlets.Unicode("0.3.24").tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        code: Optional[str] = None,
        *,
        src: Optional[str] = None,
        width: int = 500,
        height: int = 300,
        version: str = "0.3.24",
        **kwargs: Any,
    ) -> None:
        """Create a ManimWeb widget.

        The scene source is resolved in Python, so the browser always receives
        plain JavaScript. ``code`` (or ``src``) may be any of:

        * an inline JavaScript string,
        * a path to a local ``.js`` file, or
        * an ``http(s)://`` URL.

        URLs and file paths are fetched/read here at construction time; the
        detection is by value, so ``ManimWeb("https://.../scene.js")`` and
        ``ManimWeb("const s = new manim.Scene(...)")`` both do the right thing.

        Args:
            code: Inline JavaScript, a local file path, or an ``http(s)://``
                URL. Mutually exclusive with ``src``.
            src: An explicit alias for ``code`` (same accepted forms), handy
                when the intent is "load from here". Mutually exclusive with
                ``code``.
            width: Container width in pixels.
            height: Container height in pixels.
            version: The manim-web version to load from the CDN.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If neither or both of ``code`` and ``src`` are given.
        """
        if (code is None) == (src is None):
            raise ValueError("Provide exactly one of `code` or `src`.")

        source = code if code is not None else src
        super().__init__(
            code=self._resolve_source(source),
            width=width,
            height=height,
            version=version,
            **kwargs,
        )

    @staticmethod
    def _resolve_source(source: str) -> str:
        """Return scene JS: fetch a URL, read a local file, or pass JS through."""
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
