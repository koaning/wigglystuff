# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "pillow",
#     "wigglystuff==0.5.8",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import Excalidraw

    return Excalidraw, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Excalidraw

    An embedded [Excalidraw](https://excalidraw.com) whiteboard. Sketch shapes,
    arrows, text, and freehand drawings on an infinite canvas. The drawing lives on
    the `scene` traitlet, so it syncs back to Python as you edit.

    Excalidraw itself is loaded from a CDN the first time the widget renders, so this
    widget needs network access and does not work fully offline.
    """)
    return


@app.cell
def _(Excalidraw, mo):
    draw = mo.ui.anywidget(Excalidraw(height=800, theme="light"))
    draw
    return (draw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    `get_pil()` returns the drawing as a PIL image, so you can pass what you drew
    forward — into a multimodal model, save it, composite it, etc. The PNG is
    rendered in the browser and synced back, so it lags edits by up to
    `sync_throttle_ms`.
    """)
    return


@app.cell
def _(draw):
    draw.get_pil()
    return


@app.cell
def _(draw):
    # The current scene (elements / appState / files) as a dict.
    draw.scene
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Nothing is written to disk automatically. Call `save(path)` to persist the
    scene to a `.excalidraw` file, and `Excalidraw.from_file(path)` to load one back.

    ```python
    draw.save("diagram.excalidraw")
    again = Excalidraw.from_file("diagram.excalidraw")
    ```

    You can also preload a scene at construction time with `Excalidraw(scene=...)`.
    """)
    return


if __name__ == "__main__":
    app.run()
