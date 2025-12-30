import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from drawdata import ScatterWidget
    from wigglystuff import Matrix, ThreeWidget
    return Matrix, ScatterWidget, ThreeWidget, mo


@app.cell
def _(ScatterWidget, mo):
    scatter = mo.ui.anywidget(ScatterWidget())
    scatter
    return (scatter,)


@app.cell
def _(Matrix, mo, scatter):
    import numpy as np 

    arr = scatter.data_as_polars.select("x", "y")
    dicts = scatter.data_as_polars.select("x", "y", "color").to_dicts()

    mat = mo.ui.anywidget(Matrix(np.array([[1, 0, 0], [0, 1, 0]]), step=0.01))
    mat
    return dicts, mat, np


@app.cell
def _(ThreeWidget, dicts, mat, scatter):
    dim_plus = scatter.data_as_polars.select("x", "y").to_numpy() @ mat.matrix

    ThreeWidget(
        data=[{**d, "x": arr[0], "y": arr[1], "z": arr[2], "size": 5} 
              for arr, d in zip(dim_plus, dicts)],
        dark_mode=True
    )
    return (dim_plus,)


@app.cell
def _(Matrix, mo, np):
    mat_again = mo.ui.anywidget(Matrix(np.eye(3), step=0.01))
    mat_again
    return (mat_again,)


@app.cell
def _(ThreeWidget, dicts, dim_plus, mat_again):
    dim_plusplus = dim_plus @ mat_again.matrix

    ThreeWidget(
        data=[{**d, "x": arr[0], "y": arr[1], "z": arr[2], "size": 5} 
              for arr, d in zip(dim_plusplus, dicts)],
        dark_mode=True
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
