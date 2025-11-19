from pathlib import Path
from typing import Sequence

import anywidget
import traitlets


class SortableList(anywidget.AnyWidget):
    """Interactive sortable list with optional editing capabilities."""

    _esm = Path(__file__).parent / "static" / "sortable-list.js"
    _css = Path(__file__).parent / "static" / "sortable-list.css"
    value = traitlets.List(traitlets.Unicode()).tag(sync=True)
    addable = traitlets.Bool(default_value=False).tag(sync=True)
    removable = traitlets.Bool(default_value=False).tag(sync=True)
    editable = traitlets.Bool(default_value=False).tag(sync=True)

    def __init__(
        self,
        value: Sequence[str],
        *,
        addable: bool = False,
        removable: bool = False,
        editable: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            value=list(value),
            addable=addable,
            removable=removable,
            editable=editable,
            **kwargs,
        )
