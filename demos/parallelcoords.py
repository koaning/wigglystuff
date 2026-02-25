import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ParallelCoordinates

    Interactive parallel coordinates plot powered by HiPlot.
    Brush on axes to filter, drag axis labels to reorder, and right-click an axis to color by it.
    """)
    return


@app.cell
def _(mo):
    from sklearn.datasets import load_iris

    from wigglystuff import ParallelCoordinates

    iris = load_iris(as_frame=True)
    df = iris.frame

    widget = mo.ui.anywidget(ParallelCoordinates(df, height=300, color_by="target"))
    widget
    return ParallelCoordinates, widget


@app.cell
def _(mo, widget):
    n_filtered = len(widget.filtered_indices)
    n_total = len(widget.data)
    mo.md(f"**Filtered:** {n_filtered} / {n_total} rows")
    return


@app.cell
def _(widget):
    widget.filtered_as_pandas
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Scale Demo

    Example with **15,000 rows** and multiple dimensions to show large-data handling.
    """)
    return


@app.cell
def _(ParallelCoordinates, mo):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(42)
    n_rows = 15_000
    segments = rng.integers(0, 4, size=n_rows)

    big_df = pd.DataFrame(
        {
            "x0": rng.normal(segments * 0.7, 1.0),
            "x1": rng.normal(segments * 0.3, 1.1),
            "x2": rng.normal(segments * 0.5, 0.9),
            "x3": rng.normal(segments * 0.2, 1.2),
            "x4": rng.normal(segments * 0.4, 1.0),
            "x5": rng.normal(segments * 0.6, 1.0),
            "segment": segments.astype(str),
        }
    )

    widget_lg = mo.ui.anywidget(ParallelCoordinates(big_df, height=360, color_by="segment"))
    widget_lg
    return (widget_lg,)


@app.cell
def _(mo, widget_lg):
    n_filtered_large = len(widget_lg.filtered_indices)
    n_total_large = len(widget_lg.data)
    mo.md(f"**Scale demo filtered:** {n_filtered_large} / {n_total_large} rows")
    return


if __name__ == "__main__":
    app.run()
