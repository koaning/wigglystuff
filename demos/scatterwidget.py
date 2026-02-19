import marimo

__generated_with = "0.18.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ScatterWidget

    Draw data points directly in your notebook! Click or drag to paint points,
    select a class to switch colors, and use the brush size slider to control
    the spread. The data syncs back to Python as a list of dicts.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import ScatterWidget

    widget = mo.ui.anywidget(ScatterWidget(n_classes=3))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The widget exposes helper properties to convert the drawn data into
    pandas DataFrames, polars DataFrames, or numpy arrays.
    """)
    return


@app.cell
def _(widget):
    widget.data_as_pandas
    return


@app.cell
def _(widget):
    widget.data_as_polars
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Single class mode

    When you set `n_classes=1`, the widget becomes a regression tool.
    There's only one color, so `data_as_X_y` returns `X` with shape
    `(n, 1)` and `y` as a 1D array of y-values.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import ScatterWidget as SW

    regression_widget = mo.ui.anywidget(SW(n_classes=1))
    regression_widget
    return (regression_widget,)


@app.cell
def _(regression_widget):
    regression_widget.data_as_pandas
    return


if __name__ == "__main__":
    app.run()
