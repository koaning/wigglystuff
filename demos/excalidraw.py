# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "pillow",
#     "wigglystuff==0.5.8",
# ]
# ///

import marimo

__generated_with = "0.23.11"
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


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Fit-to-content on load

    When you preload a scene (via `scene=` or `from_file`), the widget fits the
    drawing into the viewport on open, so a sketch that was saved zoomed out
    reopens at the right scale instead of clipping. The scene below is wider than
    the widget at 100%, yet it opens with everything in view (and a small margin
    around it). Fit only zooms *out* — it's capped at 100%, so a small scene
    never blows up past its actual size.
    """)
    return


@app.cell
def _(Excalidraw, mo):
    def rect(id, x, y, w, h, color):
        return {
            "id": id, "type": "rectangle", "x": x, "y": y,
            "width": w, "height": h, "strokeColor": color,
            "backgroundColor": "transparent",
        }

    def label(id, x, y, w, h, text, size):
        # Excalidraw doesn't measure text on load, so text elements need an
        # explicit width/height — without them the element gets 0x0 bounds and
        # renders/fits wrong. fontFamily 6 is the normal (non-hand-drawn) font.
        return {
            "id": id, "type": "text", "x": x, "y": y, "width": w, "height": h,
            "text": text, "fontSize": size, "fontFamily": 6,
            "textAlign": "left", "verticalAlign": "top",
        }

    # A wide row of boxes, far too wide to fit at 100%; fit zooms out to show
    # them all. Wide-and-short keeps the fit width-constrained, so there's plenty
    # of vertical room and the title clears Excalidraw's floating toolbar.
    big_scene = {
        "elements": [
            label("title", 40, 40, 1200, 70, "This whole scene fits on open", 56),
            rect("r1", 40, 200, 380, 300, "#1971c2"),
            rect("r2", 540, 200, 380, 300, "#e8590c"),
            rect("r3", 1040, 200, 380, 300, "#2f9e44"),
            rect("r4", 1540, 200, 380, 300, "#9c36b5"),
        ],
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }

    mo.ui.anywidget(Excalidraw(scene=big_scene, height=500, theme="light"))
    return


if __name__ == "__main__":
    app.run()
