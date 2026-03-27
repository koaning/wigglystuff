# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "mohtml",
#     "wigglystuff==0.3.1",
# ]
# ///

import marimo

__generated_with = "0.21.1"
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
