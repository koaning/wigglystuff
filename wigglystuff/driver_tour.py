from pathlib import Path
from typing import Any, Sequence

import anywidget
import traitlets


class DriverTour(anywidget.AnyWidget):
    """Interactive guided tour widget powered by Driver.js overlays.

    Define CSS selector-based steps with popovers to guide notebook readers,
    optionally auto-starting the experience and surfacing progress indicators.
    """

    _esm = Path(__file__).parent / "static" / "driver-tour.js"
    _css = Path(__file__).parent / "static" / "driver-tour.css"

    steps = traitlets.List(traitlets.Dict()).tag(sync=True)
    auto_start = traitlets.Bool(False).tag(sync=True)
    show_progress = traitlets.Bool(True).tag(sync=True)
    active = traitlets.Bool(False).tag(sync=True)
    current_step = traitlets.Int(0).tag(sync=True)

    def __init__(
        self,
        steps: Sequence[dict] = (),
        *,
        auto_start: bool = False,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a DriverTour widget.

        Args:
            steps: List of tour step dictionaries with element and popover keys.
            auto_start: Start tour automatically on render.
            show_progress: Show step progress indicator.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(
            steps=list(steps),
            auto_start=auto_start,
            show_progress=show_progress,
            **kwargs,
        )
