---
title: "Pip: float a widget in a picture-in-picture window"
description: Pip wraps a widget and adds a button that moves it into a window floating above other windows, so it stays visible while the notebook is scrolled.
image: pip
image_alt: A scatter chart floating in a small always-on-top window above a marimo notebook, with a placeholder left in its place
---

# Pip API

`Pip` wraps a widget and adds a button to its top-right corner. Pressing that
button moves the widget into a window that floats above other windows,
including other applications, and leaves a placeholder in the notebook that
brings it back. This is the browser's [Document Picture-in-Picture][pip-api]
window, not a second browser tab.

The wrapped widget is the same object in both places, so a `Pip` can be put
around an existing widget without changing the code that reads it:

```python
import marimo as mo
from wigglystuff import GridDraw, Pip

sketch = mo.ui.anywidget(GridDraw(rows=6, cols=6, width=300, height=300))
panel = mo.ui.anywidget(Pip(sketch, width=340, height=360))
panel
```

```python
sketch.widget.dots  # the same trait, wherever the grid is drawn
```

Pop the grid out, put the floating window beside something worth copying from,
and draw in it: the clicks and drags belong to that window, and the dots land
back in the notebook.

Wrapping the child in `mo.ui.anywidget` is what makes cells that read it re-run
as it changes; a bare widget still updates in Python, but nothing re-runs.

Only a click can open the window. Closing it can be done by the reader, from
the placeholder or the window's own controls, or from Python by setting
`floating` to `False`.

[pip-api]: https://developer.mozilla.org/en-US/docs/Web/API/Document_Picture-in-Picture_API

## A separate window is a separate document

The floating window is created with the browser's
[Document Picture-in-Picture][pip-api] API. It is not a browser tab and not an
iframe: it is a document of its own, with its own `window` and `document`,
displayed in a window the operating system keeps above others. Both of this
widget's constraints follow from that.

**It exists only where the API does.** Chromium 116 and Firefox 151 implement
it; Safari does not, and there the button is not drawn and the child stays
inline. A tab is allowed a single such window, so opening a second `Pip` closes
the first, which restores its inline view. The request must also come from a
top-level page, so a notebook displayed inside an iframe cannot open one — which
is why the demo below is a link rather than an embed.

**Events and styles belong to the window they happen in.** A widget that follows
the pointer by listening on `window` — the usual way to keep tracking a drag
after the pointer leaves the element — is listening to the *notebook's* window,
and so hears nothing while it floats. Dragging such a widget does nothing until
it comes back. Widgets that capture the pointer on their own element are
unaffected, because the events never leave the element:

| Dragging works while floating | Dragging stops while floating |
| --- | --- |
| [GridDraw](grid-draw.md), [CurveEditor](curve-editor.md), [BezierCurve](bezier-curve.md), [HoverSlider](hover-slider.md), [ThreeWidget](three-widget.md) | [Knob](knob.md), [Fader](fader.md), [Matrix](matrix.md), [TangleSlider](tangle.md), [Slider2D](slider2d.md), [CircularSlider](circular-slider.md) |

Widgets driven by clicks, buttons or text entry work in both places either way.

Styles arrive by the same rule, with one thing carried across deliberately. A
widget's own stylesheet is mounted into the floating window, in that window's
realm, so it is styled there. Its light and dark rules are usually selected by
a class the notebook sets on an ancestor, which the floating document does not
have, so `Pip` copies that class over and keeps it in step with the notebook.
What is not copied is the notebook's own CSS, so a widget drawn with the
notebook's classes or variables, rather than its own, looks unstyled while
floating. No widget in this collection is.

Try it as a full page:
[demos/pip.py on molab](https://molab.marimo.io/github/koaning/wigglystuff/blob/main/demos/pip.py/wasm?utm_source=wigglystuff).

::: wigglystuff.pip.Pip

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `child` | widget | The wrapped widget; serialized to the wire as an `anywidget:<model_id>` reference. |
| `width` | `int` | Initial width of the floating window, in pixels. |
| `height` | `int` | Initial height of the floating window, in pixels. |
| `floating` | `bool` | Whether the child is currently floating. Set `False` to close the window; setting `True` is refused (needs a user gesture). |
