import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    from mohtml import div, img, tailwind_css
    from wigglystuff import Paint

    tailwind_css()
    return Paint, div, img, mo


@app.cell
def _(Paint, mo):
    widget = mo.ui.anywidget(Paint(height=550))
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(div, img, widget):
    div(img(src=widget.get_base64()), klass="bg-gray-200 p-4")
    return


@app.cell
def _(widget):
    widget.get_pil()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can also draw over existing images with this library, this can be useful when interacting with multimodal LLMs.
    """)
    return


@app.cell
def _(Paint, mo):
    redraw_widget = mo.ui.anywidget(
        Paint(
            init_image="https://marimo.io/_next/image?url=%2Fimages%2Fblog%2F8%2Fthumbnail.png&w=1920&q=75"
        )
    )
    return (redraw_widget,)


@app.cell
def _(redraw_widget):
    redraw_widget
    return


@app.cell
def _(redraw_widget):
    redraw_widget.get_pil()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
