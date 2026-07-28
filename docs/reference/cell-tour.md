---
title: "CellTour: guided tour of marimo cells"
description: CellTour builds a step-by-step walkthrough of a marimo notebook, pointing each step at a cell by index or name, in edit mode and in marimo run.
image: celltour
image_alt: CellTour widget showing a tour popover anchored to a marimo cell with previous and next buttons
---

# CellTour API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="celltour" data-demo-title="CellTour live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/celltour.webp" alt="CellTour widget showing a tour popover anchored to a marimo cell with previous and next buttons" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`CellTour` walks a reader through a marimo notebook one popover at a time. Each step
points at a cell by index (`{"cell": 0}`) or by name (`{"cell_name": "imports"}`) instead
of a hand-written CSS selector, which is what makes it easier to keep in sync than a raw
Driver.js tour. Set `auto_start` to open the tour on render, and read `active` and
`current_step` back in Python to react to where the reader has got to.

See also: [ApiDoc](api-doc.md) for putting a reference card next to the example it
documents, [EnvConfig](env-config.md) for gating a notebook on credentials before the
reader starts, and [LiveEdit](live-edit.md) for explaining what a function does pass by
pass.

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

