import json
from pathlib import Path
from typing import Optional, Union

import anywidget
import traitlets
import re

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

    def to_mermaid(self, direction: str = "TD") -> str:
        """
        Convert an Excalidraw scene dict (as returned by wigglystuff's
        `draw.scene` in marimo) into Mermaid flowchart syntax.
    
        Strategy
        --------
        - Shape elements (rectangle / diamond / ellipse) become nodes.
        - Text elements get resolved to their parent shape via the shape's
        `boundElements` (falling back to the text's own `containerId`),
        so a shape's label always comes from its bound text, not from
        guessing based on position.
        - Text elements with no `containerId` are treated as free-standing
        label nodes.
        - Arrow/line elements become edges, using `startBinding` /
        `endBinding` to find which nodes they connect. If the arrow
        itself has bound text (a label), that becomes the edge label.
        - Deleted elements (`isDeleted: True`) are ignored.
        - Color is carried over from each element's own `strokeColor` /
        `backgroundColor` / `strokeWidth` attributes (not inherited or
        guessed from bound elements) and emitted as `style` directives
        for nodes and `linkStyle` directives for edges.
        """
        state = self.scene
        elements = [e for e in state.get("elements", []) if not e.get("isDeleted")]
        by_id = {e["id"]: e for e in elements}

        SHAPE_TYPES = {"rectangle", "diamond", "ellipse"}

        def safe_id(eid: str) -> str:
            # Mermaid node ids must be alnum/underscore-ish; prefix to
            # guarantee it doesn't start with a digit.
            return "n" + re.sub(r"[^a-zA-Z0-9_]", "_", eid)

        def clean_label(text: str) -> str:
            text = (text or "").strip()
            text = text.replace('"', "'").replace("\n", "<br/>")
            return text

        def bound_text_for(element: dict) -> str:
            """Find the text bound to `element` via its boundElements list."""
            for bound in element.get("boundElements") or []:
                if bound.get("type") == "text":
                    text_el = by_id.get(bound.get("id"))
                    if text_el is not None:
                        return text_el.get("text", "")
            return ""

        def color_attrs(element: dict, force_bare: bool = False) -> tuple[str, str, int]:
            """
            Pull an element's own rendering attributes straight off the dict:
            (strokeColor, backgroundColor, strokeWidth). Excalidraw uses the
            string "transparent" for "no fill", which we normalize to
            Mermaid's `fill:none`.

            `force_bare=True` is for plain text elements: excalidraw text
            has no real border/background of its own, so we render it with
            no outline and no fill regardless of the raw attribute values.
            """
            if force_bare:
                return "none", "none", 0
            stroke = element.get("strokeColor") or "#1e1e1e"
            bg = element.get("backgroundColor") or "transparent"
            bg = "none" if bg == "transparent" else bg
            width = element.get("strokeWidth") or 1
            return stroke, bg, width

        def node_shape_wrap(label: str, shape_type: str) -> str:
            label = clean_label(label) or " "
            if shape_type == "diamond":
                return f'{{"{label}"}}'
            if shape_type == "ellipse":
                return f'(("{label}"))'
            if shape_type == "text":
                # Plain text has no real "shape" in excalidraw; still needs a
                # node wrapper for Mermaid syntax, but we suppress its
                # border/fill below via color_attrs override.
                return f'["{label}"]'
            # rectangle
            return f'["{label}"]'

        #    Collect shape nodes, using bound text (via boundElements) for labels.
        #    Color/stroke-width always come from the *shape* element itself,
        #    never from its bound text.
        nodes: dict[str, tuple[str, str, str, str, int]] = {}
        text_ids_used_as_labels: set[str] = set()

        for e in elements:
            if e.get("type") in SHAPE_TYPES:
                label = bound_text_for(e)
                stroke, bg, width = color_attrs(e)
                nodes[e["id"]] = (label, e["type"], stroke, bg, width)
                for bound in e.get("boundElements") or []:
                    if bound.get("type") == "text":
                        text_ids_used_as_labels.add(bound["id"])

        #    Free-standing text elements (no container, not already used as a
        #    label for a shape or arrow) become their own label-only nodes,
        #    colored using the text element's own strokeColor.
        for e in elements:
            if e.get("type") == "text" and e["id"] not in text_ids_used_as_labels:
                if not e.get("containerId"):
                    stroke, bg, width = color_attrs(e, force_bare=True)
                    nodes[e["id"]] = (e.get("text", ""), "text", stroke, bg, width)

        #    Arrows/lines become edges between bound elements, colored using
        #    the arrow/line element's own strokeColor + strokeWidth.
        edges = []
        for e in elements:
            if e.get("type") in ("arrow", "line"):
                start_binding = e.get("startBinding") or {}
                end_binding = e.get("endBinding") or {}
                start_id = start_binding.get("elementId")
                end_id = end_binding.get("elementId")
                if start_id and end_id:
                    label = bound_text_for(e)
                    stroke, _bg, width = color_attrs(e)
                    for bound in e.get("boundElements") or []:
                        if bound.get("type") == "text":
                            text_ids_used_as_labels.add(bound["id"])
                    edges.append((start_id, end_id, label, stroke, width))

        #  Emit Mermaid.
        lines = [f"flowchart {direction}"]

        for node_id, (label, shape_type, _stroke, _bg, _width) in nodes.items():
            lines.append(f"    {safe_id(node_id)}{node_shape_wrap(label, shape_type)}")

        edge_lines = []
        edge_styles = []  # (linkIndex, stroke, width) - index must match edge_lines order
        for start_id, end_id, label, stroke, width in edges:
            if start_id not in nodes or end_id not in nodes:
                continue  # dangling arrow, nothing to connect
            if label:
                edge_lines.append(f"    {safe_id(start_id)} -->|{clean_label(label)}| {safe_id(end_id)}")
            else:
                edge_lines.append(f"    {safe_id(start_id)} --> {safe_id(end_id)}")
            edge_styles.append((len(edge_lines) - 1, stroke, width))

        lines.extend(edge_lines)

        # Node styling: fill = backgroundColor, stroke = strokeColor.
        for node_id, (_label, _shape_type, stroke, bg, width) in nodes.items():
            lines.append(
                f"    style {safe_id(node_id)} fill:{bg},stroke:{stroke},stroke-width:{width}px"
            )

        # Edge styling: Mermaid's linkStyle addresses edges by their 0-based
        # position among --> statements, so we track that position above.
        for idx, stroke, width in edge_styles:
            lines.append(f"    linkStyle {idx} stroke:{stroke},stroke-width:{width}px")

        return "\n".join(lines)

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
