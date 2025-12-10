import marimo

__generated_with = "0.18.1"
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
    mo.callout.info(
        f"x = {widget.x:.3f}, y = {widget.y:.3f}; bounds {widget.x_bounds} / {widget.y_bounds}"
    )
    return


@app.cell
def _(mo, widget):
    def log_changes(change):
        mo.log.info("slider moved to (%s, %s)", widget.x, widget.y)

    widget.observe(log_changes)
    return


if __name__ == "__main__":
    app.run()
