# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "drawdata==0.3.8",
#     "polars==1.35.2",
#     "duckdb==1.4.2",
#     "sqlglot==28.0.0",
#     "pyarrow==22.0.0",
# ]
# ///

import marimo

__generated_with = "0.17.8"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(slider):
    a = slider.value
    return (a,)


@app.cell
def _():
    b = 2
    return (b,)


@app.cell
def _(a, b):
    a + b
    return


@app.cell
def _(mo):
    slider = mo.ui.slider(1, 10, 1)
    slider
    return (slider,)


@app.cell
def _(mo):
    from drawdata import ScatterWidget

    widget = mo.ui.anywidget(ScatterWidget())
    widget
    return (widget,)


@app.cell
def _(widget):
    df = widget.data_as_polars
    df
    return (df,)


@app.cell
def _(df, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM df
        """
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
