import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    from mohtml import div, img, tailwind_css
    from wigglystuff import WebcamCapture

    tailwind_css()
    return WebcamCapture, div, img, mo


@app.cell
def _(WebcamCapture, mo):
    widget = mo.ui.anywidget(WebcamCapture(interval_ms=1000))
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(div, img, widget):
    div(
        img(src=widget.image_base64),
        klass="bg-slate-100 border border-slate-200 rounded-2xl p-4",
    )
    return


@app.cell
def _(widget):
    widget.get_pil()
    return


if __name__ == "__main__":
    app.run()
