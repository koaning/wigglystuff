import json
from pathlib import Path
from typing import Optional, Union

import anywidget
import traitlets

DEFAULT_HEIGHT = 600


class Excalidraw(anywidget.AnyWidget):
    """An embedded [Excalidraw](https://excalidraw.com) whiteboard.

    Draw shapes, arrows, text, and freehand sketches on an infinite canvas.
    The current drawing is kept in memory on the ``scene`` traitlet as an
    Excalidraw scene dict (``elements`` / ``appState`` / ``files``). Like the
    other drawing widgets, nothing is written to disk automatically — call
    :meth:`save` when you want to persist, and load with :meth:`from_file`.

    Args:
        scene: Optional Excalidraw scene dict to preload the canvas with.
        height: Canvas height in pixels.
        sync_throttle_ms: Minimum delay between syncing edits back to Python.
        theme: ``"light"`` (default) or ``"dark"``. Set it to ``""`` to instead
            follow the notebook's theme.

    Example:
        ```python
        import marimo as mo
        from wigglystuff import Excalidraw

        draw = mo.ui.anywidget(Excalidraw())
        draw
        ```

        After sketching something:

        ```python
        draw.save("diagram.excalidraw")          # write to disk
        again = Excalidraw.from_file("diagram.excalidraw")  # load it back
        again.save()                              # write back to diagram.excalidraw
        again.save("other.excalidraw")            # save elsewhere (and remember it)
        ```
    """

    # Excalidraw's CSS is bundled into the JS and injected into the shadow root
    # at render time (anywidget mounts inside a shadow DOM, where a sibling _css
    # file never reaches the widget), so there is no separate _css here.
    _esm = Path(__file__).parent / "static" / "excalidraw.js"

    scene = traitlets.Dict({}).tag(sync=True)
    image_base64 = traitlets.Unicode("").tag(sync=True)
    theme = traitlets.Unicode("").tag(sync=True)
    height = traitlets.Int(DEFAULT_HEIGHT).tag(sync=True)
    sync_throttle_ms = traitlets.Int(1000).tag(sync=True)

    def __init__(
        self,
        scene: Optional[dict] = None,
        height: int = DEFAULT_HEIGHT,
        sync_throttle_ms: int = 1000,
        theme: str = "light",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.height = height
        self.sync_throttle_ms = sync_throttle_ms
        self.theme = theme
        self.source_path: Optional[Path] = None
        if scene is not None:
            self.scene = scene

    def get_scene(self) -> dict:
        """Return the current Excalidraw scene as a dict."""
        return dict(self.scene)

    def get_image_base64(self) -> str:
        """Return the current drawing as a PNG data URL (empty if nothing drawn)."""
        return self.image_base64

    def get_pil(self):
        """Return the current drawing as a PIL Image, or ``None`` if empty.

        Handy for passing what you drew forward — e.g. into a multimodal model.
        The PNG is rendered in the browser and synced back, so it lags edits by
        up to ``sync_throttle_ms``.
        """
        if not self.image_base64:
            return None
        import base64
        import io

        from PIL import Image

        payload = self.image_base64.split(",", 1)[-1]
        return Image.open(io.BytesIO(base64.b64decode(payload)))

    def to_json(self) -> str:
        """Return the current scene serialized as a JSON string."""
        return json.dumps(self.scene)

    def save(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Write the current scene to a ``.excalidraw`` JSON file and return where.

        Pass ``path`` to choose the destination; it is remembered on
        ``source_path``, so later calls — and widgets created via
        :meth:`from_file` — can call ``save()`` with no argument to write back
        to the same file. This widget never writes on its own: in marimo,
        putting ``save()`` in its own cell makes it *effectively* autosave,
        because marimo (not this method) re-runs that cell whenever the widget
        changes, so the file tracks what you draw. The returned absolute path is
        shown as the cell output, so it is always clear which file was written.
        """
        if path is not None:
            self.source_path = Path(path)
        if self.source_path is None:
            raise ValueError(
                "save() needs a path: either pass one, e.g. "
                'save("diagram.excalidraw"), or create the widget with '
                "Excalidraw.from_file(...) so the source path is known."
            )
        Path(self.source_path).write_text(self.to_json(), encoding="utf-8")
        return Path(self.source_path).resolve()

    @classmethod
    def from_file(cls, path: Union[str, Path], **kwargs) -> "Excalidraw":
        """Create an :class:`Excalidraw` preloaded with the scene at ``path``.

        The path is remembered on ``source_path`` so you can call
        :meth:`save` with no argument to write edits back to the same file.
        """
        scene = json.loads(Path(path).read_text(encoding="utf-8"))
        widget = cls(scene=scene, **kwargs)
        widget.source_path = Path(path)
        return widget
