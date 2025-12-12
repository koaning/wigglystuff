from typing import Any, Sequence

from .driver_tour import DriverTour


class CellTour(DriverTour):
    """Simplified tour widget for marimo notebooks.

    A friendlier API for creating guided tours that targets cells by index or name.

    Parameters
    ----------
    steps:
        Sequence of step dictionaries. Each step should have either:
        - cell: int, 0-indexed cell number to highlight, OR
        - cell_name: str, the data-cell-name attribute of the cell
        Plus:
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
    >>> # Using cell indices
    >>> tour = CellTour(steps=[
    ...     {"cell": 0, "title": "Imports", "description": "Load libraries"},
    ...     {"cell": 2, "title": "Processing", "description": "Data transformation"},
    ... ])

    >>> # Using cell names (requires naming cells in marimo)
    >>> tour = CellTour(steps=[
    ...     {"cell_name": "imports", "title": "Imports", "description": "Load libraries"},
    ...     {"cell_name": "process", "title": "Processing", "description": "Transform data"},
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
        cell_name = step.get("cell_name")

        if cell_index is None and cell_name is None:
            raise ValueError(
                "Each step must have either a 'cell' key with a cell index "
                "or a 'cell_name' key with a cell name"
            )

        popover = {
            "title": step.get("title", ""),
            "description": step.get("description", ""),
            "position": step.get("position", "bottom"),
        }

        # Use cell_name selector if provided, otherwise use index
        if cell_name is not None:
            return {
                "element": f'[data-cell-name="{cell_name}"]',
                "popover": popover,
            }
        else:
            return {
                "element": ".marimo-cell",
                "index": cell_index,
                "popover": popover,
            }
