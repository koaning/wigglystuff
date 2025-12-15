import marimo

__generated_with = "0.18.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import altair as alt

    from wigglystuff import Matrix
    return Matrix, alt, mo, np, pd


@app.cell
def _(Matrix, mo, np, pd):
    pca_mat = mo.ui.anywidget(Matrix(np.random.normal(0, 1, size=(3, 2)), step=0.1))
    rgb_mat = np.random.randint(0, 255, size=(1000, 3))
    color = ["#{0:02x}{1:02x}{2:02x}".format(r, g, b) for r, g, b in rgb_mat]

    rgb_df = pd.DataFrame(
        {"r": rgb_mat[:, 0], "g": rgb_mat[:, 1], "b": rgb_mat[:, 2], "color": color}
    )
    return color, pca_mat, rgb_mat


@app.cell
def _(alt, color, mo, pca_mat, pd, rgb_mat):
    X_tfm = rgb_mat @ pca_mat.matrix
    df_pca = pd.DataFrame({"x": X_tfm[:, 0], "y": X_tfm[:, 1], "c": color})
    pca_chart = (
        alt.Chart(df_pca)
        .mark_point()
        .encode(x="x", y="y", color=alt.Color("c:N", scale=None))
        .properties(width=400, height=400)
    )

    mo.vstack(
        [
            mo.md("""
    ### PCA demo with `Matrix` 

    Ever want to do your own PCA? Try to figure out a mapping from a 3d color map to a 2d representation with the transformation matrix below."""),
            mo.hstack([pca_mat, pca_chart]),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
