import marimo

__generated_with = "0.18.1"
app = marimo.App(width="large")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from wigglystuff import Matrix

    mean_widget = mo.ui.anywidget(Matrix(rows=1, cols=2, step=0.1))
    cov_widget = mo.ui.anywidget(Matrix(matrix=np.eye(2), mirror=True, step=0.05))
    return cov_widget, mean_widget, mo, np, pd


@app.cell
def _(mean_widget):
    mean_widget
    return


@app.cell
def _(cov_widget):
    cov_widget
    return


@app.cell
def _(mean_widget, mo, np):
    mean = np.array(mean_widget.matrix).reshape(-1)
    mo.callout.tip(
        f"Mean vector = [{mean[0]:.2f}, {mean[1]:.2f}] (editable via the first matrix)"
    )
    return


@app.cell
def _(cov_widget, mo, np):
    cov = np.array(cov_widget.matrix).reshape(2, 2)
    mo.callout.info(
        f"Covariance matrix = {cov.tolist()}"
    )
    return cov


@app.cell
def _(cov, mean_widget, mo, np, pd):
    samples = np.random.multivariate_normal(np.array(mean_widget.matrix).reshape(-1), cov, 500)
    df = pd.DataFrame(samples, columns=["x", "y"])
    mo.table(df.head())
    return


if __name__ == "__main__":
    app.run()
