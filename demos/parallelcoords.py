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
    widget = mo.ui.anywidget(
        ParallelCoordinates(df, height=300, color_by="target")
    )
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    n_filtered = len(widget.widget.filtered_indices)
    n_total = len(widget.widget.data)
    mo.md(f"**Filtered:** {n_filtered} / {n_total} rows")
    return


@app.cell
def _(widget):
    widget.widget.filtered_as_pandas
    return


if __name__ == "__main__":
    app.run()
