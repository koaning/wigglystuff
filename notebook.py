import marimo

__generated_with = "0.9.10"
app = marimo.App()


@app.cell
def __(alt, df, df_base, mo, slider_2d):
    chart = (
        alt.Chart(df_base).mark_point(color="gray").encode(x="x", y="y") + 
        alt.Chart(df).mark_point().encode(x="x", y="y")
    ).properties(width=300, height=300)

    mo.vstack([
        mo.md("""
    ## `Slider2D` demo

    ```python
    from wigglystuff import Slider2D

    slider_2d = Slider2D(width=300, height=300)
    ```

    This demo contains a two dimensional slider. The thinking is that sometimes you want to be able to make changes to two variables at the same time. The output is always standardized to the range of -1 to 1, but you can always use custom code to adapt this."""),
        mo.hstack([slider_2d, chart])
    ])
    return (chart,)


@app.cell
def __(arr, np):
    np.array(arr.matrix).reshape(-1)
    return


@app.cell
def __(alt, arr, df_orig, mat, mo, np, pd):
    x_sim = np.random.multivariate_normal(
        np.array(arr.matrix).reshape(-1), 
        np.array(mat.matrix), 
        2500
    )
    df_sim = pd.DataFrame({"x": x_sim[:, 0], "y": x_sim[:, 1]})

    chart_sim = (
        alt.Chart(df_sim).mark_point().encode(x="x", y="y") + 
        alt.Chart(df_orig).mark_point(color="gray").encode(x="x", y="y")
    )

    mo.vstack([
        mo.md("""
    ## `Matrix` demo

    ```python
    from wigglystuff import Matrix

    arr = Matrix(rows=1, cols=2, triangular=True, step=0.1)
    mat = Matrix(matrix=np.eye(2), triangular=True, step=0.1)
    ```

    This demo contains a representation of a two dimensional gaussian distribution. You can adapt the center by changing the first array that represents the mean and the variance can be updated by alterering the second one that represents the covariance matrix. Notice how the latter matrix has a triangular constraint."""),
        mo.hstack([arr, mat, chart_sim])
    ])
    return chart_sim, df_sim, x_sim


@app.cell
def __(mo):
    mo.md(r"""## Appendix with all supporting code""")
    return


@app.cell
def __():
    import altair as alt
    import marimo as mo
    import micropip
    import numpy as np
    import pandas as pd

    # await micropip.install("wigglystuff==0.1.1")
    return alt, micropip, mo, np, pd


@app.cell
def __(mo, np):
    from wigglystuff import Matrix

    mat = mo.ui.anywidget(Matrix(matrix=np.eye(2), triangular=True, step=0.1))
    arr = mo.ui.anywidget(Matrix(rows=1, cols=2, triangular=True, step=0.1))
    return Matrix, arr, mat


@app.cell
def __(Matrix, mo, np):
    x1 = mo.ui.anywidget(Matrix(matrix=np.eye(2), step=0.1))
    x2 = mo.ui.anywidget(Matrix(matrix=np.random.random((2, 2)), step=0.1))
    return x1, x2


@app.cell
def __(mo):
    from wigglystuff import Slider2D

    slider_2d = mo.ui.anywidget(Slider2D(width=300, height=300))
    return Slider2D, slider_2d


@app.cell
def __(np, pd, slider_2d):
    df = pd.DataFrame({
        "x": np.random.normal(slider_2d.x * 10, 1, 2000), 
        "y": np.random.normal(slider_2d.y * 10, 1, 2000)
    })
    return (df,)


@app.cell
def __(np, pd):
    df_base = pd.DataFrame({
        "x": np.random.normal(0, 1, 2000), 
        "y": np.random.normal(0, 1, 2000)
    })
    return (df_base,)


@app.cell
def __(np, pd):
    x_orig = np.random.multivariate_normal(np.array([0, 0]), np.array([[1, 0], [0, 1]]), 2500)
    df_orig = pd.DataFrame({"x": x_orig[:, 0], "y": x_orig[:, 1]})
    return df_orig, x_orig


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
