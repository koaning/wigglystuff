# CubeWidget Selection Visual Design

## Goal

Make CubeWidget selections immediately legible without losing the cube's spatial context. The visual treatment should feel compact and restrained like the Paint widget while preserving the widget's existing axis-locking behavior and state model.

## Approved Direction

Use the strong-focus treatment from mockup A with the smaller 5.5 px point from mockup B.

The cube has two visual modes:

- With no locked axes, render the normal cube structure and the three colored axes.
- Once an axis is locked, render every structural cube line as a quiet gray dashed scaffold. Keep the three colored axes solid and visually clean. Render the active selection geometry above both.

The dashed scaffold applies to every structural cube line. There is no separate solid-front-edge treatment during selection.

## Rendering Order

Render SVG layers in this order:

1. Structural cube lines
2. Neutral cutouts beneath the three colored axes
3. The three colored axes
4. Selected plane
5. Neutral cutout beneath the selected line
6. Selected line
7. Selected point
8. Axis order badges

This order guarantees that dashed cube lines cannot show through the colored axes or cross over a selection. The neutral cutouts use the widget surface color, including its dark-theme value.

## Selection Styling

- Structural cube lines: gray, dashed, and strongly faded whenever at least one axis is locked.
- Colored axes: solid, faded less than the cube structure, and drawn over a thin surface-colored cutout.
- Plane: axis-colored translucent fill with a matching outline.
- Line: axis-colored solid stroke over a wider surface-colored cutout.
- Point: axis-colored circle with a 5.5 px radius and a thin surface-colored outline.
- Axis badges: keep their axis colors and lock-order numbers.

Plane and line strength do not decrease when a narrower selection is added. There is no progressive fading between the plane, line, and point states.

## Controls

Keep the controls in a compact floating card beneath the cube, following the visual density of the Paint widget.

Each locked axis gets one slider row with:

- The display name in the axis color
- A neutral track with an axis-colored filled portion
- A small axis-colored thumb
- The current value aligned at the right

Use the existing axis palette consistently in the widget and cannonball demo chart:

- X / first axis: `#e74c3c`
- Y / second axis: `#27ae60`
- Z / third axis: `#3498db`

Retain the small reset control in the widget toolbar. Do not change locking order, slider behavior, or Python state synchronization.

## Theme Behavior

Define the scaffold, surface, border, text, track, cutout, and shadow colors through widget-scoped CSS variables. Override them for `.dark`, `.dark-theme`, and `[data-theme="dark"]` ancestors. The cutouts must always match the active surface color so they read as separation rather than white outlines.

## Behavioral Scope

This is a presentation change only. It does not change:

- Axis clicking and ordered plane → line → point locking
- Smooth slider updates
- Reset behavior
- `locked_order`, `axis_values`, `plane`, `line`, or `point`
- Python helpers or configuration validation

## Verification

Python tests continue to cover configuration, locking, derived outputs, supplied values, unlocking, reset, and invalid input.

The focused browser test should additionally verify:

- The cube renders before any selection
- Structural cube lines become dashed after the first lock
- All structural lines use the same selected-state treatment
- Colored axes remain solid and have a cutout layer beneath them
- Selection layers follow the required SVG order
- The selected point uses a 5.5 px radius
- Slider fills and labels use the matching axis color
- Reset restores the unselected cube treatment
- Light and dark surface variables keep cutouts visually correct

The demo remains dataframe-driven, and its chart series retain the same axis colors as the widget sliders.
