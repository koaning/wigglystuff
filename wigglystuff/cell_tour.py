from typing import Any, Sequence

from .driver_tour import DriverTour


class CellTour(DriverTour):
    """Simplified tour widget for marimo notebooks.

    Wraps ``DriverTour`` with cell-aware step helpers so you can reference
    marimo cells by index or `data-cell-name` attributes.

    Examples:
        Using cell indices:

        ```python
        tour = CellTour(steps=[
            {"cell": 0, "title": "Imports", "description": "Load libraries"},
            {"cell": 2, "title": "Processing", "description": "Data transformation"},
        ])
        tour
        ```

        Using cell names (requires naming cells in marimo):

        ```python
        tour = CellTour(steps=[
            {"cell_name": "imports", "title": "Imports", "description": "Load libraries"},
            {"cell_name": "process", "title": "Processing", "description": "Transform data"},
        ])
        tour
        ```
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
