---
title: "FloatingPanel: pin any marimo content above the notebook"
description: FloatingPanel wraps any marimo content in a draggable panel that stays pinned to the viewport while the notebook scrolls, and minimizes to just its header.
image: floatingpanel
image_alt: FloatingPanel floating a slider and a dial above a scrolling notebook
---

# FloatingPanel API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="floating_panel" data-demo-title="FloatingPanel live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/floatingpanel.webp" alt="FloatingPanel floating a slider and a dial above a scrolling notebook" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`FloatingPanel` wraps any marimo content in a `position: fixed` panel that stays in view
while the notebook scrolls, is draggable by its header, and minimizes to just that header
with the `−` toggle. It is a marimo display helper rather than an `AnyWidget`, and the
wrapped content stays live — keep your own reference and read `.value` as usual.

Unlike [Pip](pip.md), which moves a widget into a separate Picture-in-Picture window, the
panel is an ordinary element in the page, so it also works inside an iframe such as molab.

See also: [Pip](pip.md) for floating a widget in a real OS window, and [Hint](hint.md) and
[WidgetDAG](widget-dag.md) for other marimo-only display helpers.

::: wigglystuff.floating_panel.FloatingPanel

## Parameters

`FloatingPanel` is a display helper, not an `AnyWidget`, so it has no synced traitlets.
Everything is set once at construction.

| Parameter | Type | Notes |
| --- | --- | --- |
| `child` | any | The content to float. Anything marimo can render: an `mo.ui` element, an `mo.vstack`/`mo.hstack` layout, a figure, an image, another wigglystuff widget, or plain markdown. |
| `corner` | `str` | Where the panel starts before it is dragged: `"top-left"`, `"top-right"`, `"bottom-left"` or `"bottom-right"`. Anything else raises `ValueError`. |
| `width` | `int` or `None` | Panel width in pixels. Defaults to `None`, which shrink-wraps the panel to its content — the right choice for most content, since marimo widgets keep their own width. Set an integer for a fixed width, e.g. to reflow long text. A non-positive width raises `ValueError`. |
| `collapsed` | `bool` | Start minimized, showing only the draggable header. The header's `−`/`+` toggle collapses and expands it; nothing is ever fully dismissed. |

## Notes

`FloatingPanel` is a marimo-only display helper. A companion overlay reaches into
marimo's rendered DOM to build the drag header, pin the panel, and — crucially —
portal the panel to `document.body` so its `z-index` wins over every cell (a
panel left inside a cell is painted under any cell marimo raises on hover). It is
not wired for plain Jupyter and raises a clear `RuntimeError` there. Both
`marimo edit` and `marimo run` work; marimo *script* mode (`python demo.py`) does
not, because there is no rendered DOM to draw into.

The floated content stays live and reactive. Keep your own reference to it and
read `.value` as usual — `FloatingPanel` never sits between you and your data:

```python
slider = mo.ui.slider(1, 10, label="N")
FloatingPanel(slider, corner="top-right")   # in one cell
slider.value                                 # still works in another
```

A panel can still be covered by marimo's *own* fixed chrome (the top search bar,
the corner action buttons); just drag it to a clear spot.
