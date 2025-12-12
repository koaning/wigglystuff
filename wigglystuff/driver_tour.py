from pathlib import Path
from typing import Any, Sequence

import anywidget
import traitlets


class DriverTour(anywidget.AnyWidget):
    """Interactive guided tour widget using Driver.js.

    Creates product tours and guided highlights for notebook elements as an
    alternative to markdown documentation. Define tour steps with CSS selectors
    and popovers to guide users through your notebook.

    Parameters
    ----------
    steps:
        Sequence of tour step dictionaries. Each step should have:
        - element: CSS selector string (optional, can be None for overlay-only)
        - popover: dict with title, description, and optional position
    auto_start:
        If True, tour starts automatically when widget is rendered.
        If False (default), shows a "Start Tour" button.
    show_progress:
        If True (default), displays progress indicator like "Step 2 of 5".
    active:
        Read-only flag indicating if tour is currently running.
    current_step:
        Read-only index of the current step in the tour.

    Examples
    --------
    >>> tour = DriverTour(steps=[
    ...     {
    ...         "element": "#cell-1",
    ...         "popover": {
    ...             "title": "Load Data",
    ...             "description": "This cell imports the dataset",
    ...             "position": "bottom"
    ...         }
    ...     },
    ...     {
    ...         "element": "#cell-2",
    ...         "popover": {
    ...             "title": "Process Data",
    ...             "description": "Here we clean and transform the data"
    ...         }
    ...     }
    ... ])
    >>> tour
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
