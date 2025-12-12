from typing import Any, Sequence

from .driver_tour import DriverTour


class CellTour(DriverTour):
    """Simplified tour widget for marimo notebooks.

    A friendlier API for creating guided tours that targets cells by index.

    Parameters
    ----------
    steps:
        Sequence of step dictionaries. Each step should have:
        - cell: int, 0-indexed cell number to highlight
        - title: str, popover title
        - description: str, popover description
        - position: str, optional popover position (default "bottom")
    auto_start:
        If True, tour starts automatically when widget is rendered.
        If False (default), shows a "Start Tour" button.
    show_progress:
        If True (default), displays progress indicator like "Step 2 of 5".

    Examples
    --------
    >>> tour = CellTour(steps=[
    ...     {"cell": 0, "title": "Imports", "description": "Load libraries"},
    ...     {"cell": 2, "title": "Processing", "description": "Data transformation"},
    ... ])
    >>> tour
    """

    def __init__(
        self,
        steps: Sequence[dict] = (),
        *,
        auto_start: bool = False,
        show_progress: bool = True,
        **kwargs: Any,
    ) -> None:
        """Create a CellTour widget.

        Args:
            steps: List of step dictionaries with cell, title, description keys.
            auto_start: Start tour automatically on render.
            show_progress: Show step progress indicator.
            **kwargs: Forwarded to ``DriverTour``.
        """
        transformed_steps = [self._transform_step(step) for step in steps]
        super().__init__(
            steps=transformed_steps,
            auto_start=auto_start,
            show_progress=show_progress,
            **kwargs,
        )

    @staticmethod
    def _transform_step(step: dict) -> dict:
        """Transform a simplified step to DriverTour format."""
        cell_index = step.get("cell")
        if cell_index is None:
            raise ValueError("Each step must have a 'cell' key with a cell index")

        return {
            "element": ".marimo-cell",
            "index": cell_index,
            "popover": {
                "title": step.get("title", ""),
                "description": step.get("description", ""),
                "position": step.get("position", "bottom"),
            },
        }
