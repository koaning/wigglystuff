"""TextHighlight widget for displaying text with highlighted entity spans."""

from pathlib import Path
from typing import Any

import anywidget
import traitlets

DEFAULT_PALETTE = [
    "#7aacfe",  # blue
    "#ff8c69",  # salmon
    "#7dcea0",  # green
    "#f0b27a",  # orange
    "#bb8fce",  # purple
    "#f7dc6f",  # yellow
    "#85c1e9",  # sky
    "#f1948a",  # pink
    "#82e0aa",  # mint
    "#d7bde2",  # lavender
]


class TextHighlight(anywidget.AnyWidget):
    """Text display with highlighted entity spans, like NER visualization.

    Renders text with colored highlights for labeled entity spans. Supports
    interactive adding and removing of entities, overlap handling, and
    token-level or character-level selection.

    Examples:
        ```python
        widget = TextHighlight(
            text="Barack Obama went to Washington",
            labels=["PER", "LOC"],
            entities=[
                {"text": "Barack Obama", "label": "PER", "start": 0, "end": 12},
                {"text": "Washington", "label": "LOC", "start": 21, "end": 31},
            ],
        )
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "text-highlight.js"
    _css = Path(__file__).parent / "static" / "text-highlight.css"

    text = traitlets.Unicode("").tag(sync=True)
    entities = traitlets.List([]).tag(sync=True)
    labels = traitlets.List(traitlets.Unicode()).tag(sync=True)
    color_map = traitlets.Dict({}).tag(sync=True)
    allow_overlap = traitlets.Bool(False).tag(sync=True)
    selection_mode = traitlets.Unicode("token").tag(sync=True)
    editable = traitlets.Bool(True).tag(sync=True)
    active_label = traitlets.Unicode("").tag(sync=True)
    selected_entity = traitlets.Int(-1).tag(sync=True)

    def __init__(
        self,
        text: str = "",
        *,
        entities: list[dict] | None = None,
        labels: list[str] | None = None,
        color_map: dict[str, str] | None = None,
        allow_overlap: bool = False,
        selection_mode: str = "token",
        editable: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a TextHighlight widget.

        Args:
            text: The full text to display.
            entities: List of entity dicts, each with ``text``, ``label``,
                ``start``, and ``end`` keys.
            labels: Available label strings for annotation.
            color_map: Optional mapping of label name to hex color.
                Missing labels get auto-assigned colors from a default palette.
            allow_overlap: Whether entity spans may overlap.
            selection_mode: ``"token"`` to snap selections to whitespace word
                boundaries, or ``"character"`` for arbitrary spans.
            editable: Set ``False`` for read-only display.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if labels is None:
            labels = []
        if entities is None:
            entities = []
        if color_map is None:
            color_map = {}

        resolved_map = dict(color_map)
        for i, label in enumerate(labels):
            if label not in resolved_map:
                resolved_map[label] = DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]

        super().__init__(
            text=text,
            entities=entities,
            labels=labels,
            color_map=resolved_map,
            allow_overlap=allow_overlap,
            selection_mode=selection_mode,
            editable=editable,
            **kwargs,
        )

    @traitlets.validate("selection_mode")
    def _validate_selection_mode(self, proposal: dict[str, Any]) -> str:
        value = proposal["value"]
        if value not in ("token", "character"):
            raise traitlets.TraitError(
                f"selection_mode must be 'token' or 'character', got {value!r}"
            )
        return value

    @traitlets.observe("labels")
    def _on_labels_change(self, change: Any) -> None:
        """Auto-fill color_map for any new labels."""
        resolved = dict(self.color_map)
        changed = False
        for i, label in enumerate(change["new"]):
            if label not in resolved:
                resolved[label] = DEFAULT_PALETTE[i % len(DEFAULT_PALETTE)]
                changed = True
        if changed:
            self.color_map = resolved

    def _has_overlap(self, start: int, end: int, exclude_index: int = -1) -> bool:
        for i, ent in enumerate(self.entities):
            if i == exclude_index:
                continue
            if start < ent["end"] and end > ent["start"]:
                return True
        return False

    def add_entity(self, start: int, end: int, label: str) -> None:
        """Programmatically add an entity span.

        Args:
            start: Start character offset (inclusive).
            end: End character offset (exclusive).
            label: The entity label (must be in ``labels``).

        Raises:
            ValueError: If the label is unknown, offsets are invalid,
                or the span overlaps an existing entity when ``allow_overlap``
                is ``False``.
        """
        if label not in self.labels:
            raise ValueError(f"Unknown label {label!r}. Known labels: {self.labels}")
        if start < 0 or end > len(self.text) or start >= end:
            raise ValueError(f"Invalid span [{start}, {end}) for text of length {len(self.text)}")
        if not self.allow_overlap and self._has_overlap(start, end):
            raise ValueError(f"Span [{start}, {end}) overlaps an existing entity")
        entity = {
            "text": self.text[start:end],
            "label": label,
            "start": start,
            "end": end,
        }
        self.entities = [*self.entities, entity]

    def remove_entity(self, index: int) -> None:
        """Remove entity at the given index.

        Args:
            index: Index into the ``entities`` list.
        """
        ents = list(self.entities)
        del ents[index]
        self.entities = ents

    def clear_entities(self) -> None:
        """Remove all entities."""
        self.entities = []
