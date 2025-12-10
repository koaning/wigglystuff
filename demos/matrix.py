import marimo

__generated_with = "0.18.3"
app = marimo.App(width="large")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from wigglystuff import Matrix

    mean_widget = mo.ui.anywidget(Matrix(rows=1, cols=2, step=0.1))
    cov_widget = mo.ui.anywidget(Matrix(matrix=np.eye(2), mirror=True, step=0.05))
    return cov_widget, mean_widget


@app.cell
def _(mean_widget):
    mean_widget
    return


@app.cell
def _(cov_widget):
    cov_widget
    return


@app.cell
def _(mean_widget):
    mean_widget.matrix
    return


@app.cell
def _(cov_widget):
    cov_widget.matrix
    return


if __name__ == "__main__":
    app.run()
