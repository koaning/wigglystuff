import marimo

__generated_with = "0.18.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import Slider2D

    widget = mo.ui.anywidget(
        Slider2D(
            width=320,
            height=320,
            x_bounds=(-2.0, 2.0),
            y_bounds=(-1.0, 1.5),
        )
    )
    return mo, widget


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    mo.callout(
        f"x = {widget.x:.3f}, y = {widget.y:.3f}; bounds {widget.x_bounds} / {widget.y_bounds}"
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
