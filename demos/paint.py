# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "mohtml",
#     "pillow",
#     "wigglystuff",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from mohtml import div, img
    from wigglystuff import Paint

    return Paint, div, img, mo


@app.cell
def _(Paint, mo):
    widget = mo.ui.anywidget(Paint(height=400, width=400))
    widget
    return (widget,)


@app.cell
def _(widget):
    widget.get_pil()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    You can also draw over existing images. This is handy when annotating images for multimodal LLMs.
    """)
    return


@app.cell
def _(Paint, mo):
    annotate = mo.ui.anywidget(
        Paint(
            init_image="https://picsum.photos/id/237/300/200",
            height=300,
        )
    )
    annotate
    return (annotate,)


@app.cell
def _(annotate):
    annotate.get_pil()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Set `store_background=False` for transparent PNG output. The checkerboard in the canvas indicates transparency.
    """)
    return


@app.cell
def _(Paint, mo):
    transparent = mo.ui.anywidget(Paint(height=250, width=300, store_background=False))
    transparent
    return (transparent,)


@app.cell
def _(div, img, transparent):
    div(
        img(src=transparent.get_base64()),
        style="background: repeating-conic-gradient(#d0d0d0 0% 25%, #f0f0f0 0% 50%) 0 0 / 16px 16px; padding: 16px; border-radius: 8px; display: inline-block;",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    You can also swap the canvas image after construction with `replace_with_pil(...)`. This wipes any existing strokes — the canvas has no separate background layer — and resizes the image to the widget's `(width, height)` if needed.

    This is handy when you want to keep drawing on top of the output of an image model: feed the current canvas into a model (e.g. via `get_pil()`), then pipe the model's PIL output back in with `replace_with_pil(...)` to continue iterating.
    """)
    return


@app.cell
def _(Paint, mo):
    swap = mo.ui.anywidget(Paint(height=200, width=300))
    swap
    return (swap,)


@app.cell
def _(swap):
    from PIL import Image

    swap.replace_with_pil(Image.new("RGB", (swap.width, swap.height), "tomato"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Pass `rainbow_brush=True` to add an extra spray tool to the toolbar. Each particle samples a random hue, which is handy when you want noisy, multi-color inputs for an image model.
    """)
    return


@app.cell
def _(Paint, mo):
    rainbow = mo.ui.anywidget(Paint(height=300, width=400, rainbow_brush=True))
    rainbow
    return (rainbow,)


@app.cell
def _(rainbow):
    rainbow.get_pil()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    You can trim the toolbar down to just the controls you want. Each tool has a
    boolean flag (`brush`, `marker`, `eraser`, `rainbow_brush`) and the color
    picker can be hidden with `color_picker=False`. When the picker is hidden,
    drawing uses the `color` traitlet, which is two-way synced with the picker
    when it *is* shown — so you can preset it and read it back from Python.
    """)
    return


@app.cell
def _(Paint, mo):
    trimmed = mo.ui.anywidget(
        Paint(
            height=300,
            width=400,
            marker=False,
            eraser=False,
            color_picker=False,
            color="#e11d48",
        )
    )
    trimmed
    return (trimmed,)


@app.cell
def _(trimmed):
    trimmed.color
    return


if __name__ == "__main__":
    app.run()
