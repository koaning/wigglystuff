# CellTour API


 Bases: `DriverTour`


Simplified tour widget for marimo notebooks.


Wraps `DriverTour` with cell-aware step helpers so you can reference marimo cells by index or `data-cell-name` attributes.



Using cell indices:


```
from wigglystuff import CellTour

tour = CellTour(steps=[
    {"cell": 0, "title": "Imports", "description": "Load libraries"},
    {"cell": 2, "title": "Processing", "description": "Data transformation"},
])
tour
```


Using cell names (requires naming cells in marimo):


```
tour = CellTour(steps=[
    {"cell_name": "imports", "title": "Imports", "description": "Load libraries"},
    {"cell_name": "process", "title": "Processing", "description": "Transform data"},
])
tour
```


Create a CellTour widget.


  Source code in `wigglystuff/cell_tour.py`

```
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
```


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `steps` | `list[dict]` | DriverTour-style steps (CellTour inputs are normalized). |
| `auto_start` | `bool` | Start tour automatically on render. |
| `show_progress` | `bool` | Show progress indicator when true. |
| `active` | `bool` | Whether the tour is currently running. |
| `current_step` | `int` | Index of the active step. |
