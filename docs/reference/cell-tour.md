# CellTour API

::: wigglystuff.cell_tour.CellTour

`CellTour` works in both marimo edit mode and app mode (`marimo run` /
molab). The cell selectors it emits (`.marimo-cell` and
`[data-cell-name="…"]`) require marimo `>= 0.23`, when app mode started
rendering those markers on cell containers.

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `steps` | `list[dict]` | DriverTour-style steps (CellTour inputs are normalized). |
| `auto_start` | `bool` | Start tour automatically on render. |
| `show_progress` | `bool` | Show progress indicator when true. |
| `active` | `bool` | Whether the tour is currently running. |
| `current_step` | `int` | Index of the active step. |

