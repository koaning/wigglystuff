# CellTour API

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `steps` | `list[dict]` | DriverTour-style steps (CellTour inputs are normalized). |
| `auto_start` | `bool` | Start tour automatically on render. |
| `show_progress` | `bool` | Show progress indicator when true. |
| `active` | `bool` | Whether the tour is currently running. |
| `current_step` | `int` | Index of the active step. |

::: wigglystuff.cell_tour.CellTour
