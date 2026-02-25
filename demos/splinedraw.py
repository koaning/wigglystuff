import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np

    return mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## SplineDraw

    Draw scatter points and see a spline curve fitted through them.
    The spline is computed in Python, so you can use any fitting function.
    By default a Gaussian kernel smoother is used.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import SplineDraw

    basic_widget = mo.ui.anywidget(SplineDraw())
    basic_widget
    return SplineDraw, basic_widget


@app.cell
def _(basic_widget):
    curves = basic_widget.curve_as_numpy
    total_pts = sum(len(x) for x, y in curves.values())
    f"Curve has {total_pts} points, drawn {len(basic_widget.data)} scatter points"
    return (curves, total_pts)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Multiple Classes

    With `n_classes > 1`, each class gets its own independent spline curve
    drawn in the matching color. Try drawing points with different classes.
    """)
    return


@app.cell
def _(SplineDraw, mo):
    multi_widget = mo.ui.anywidget(SplineDraw(n_classes=2))
    multi_widget
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_curves = multi_widget.curve_as_numpy
    info = ", ".join(f"{c}: {len(x)} pts" for c, (x, y) in multi_curves.items())
    info if info else "Draw some points to see curves"
    return (info, multi_curves)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Custom Spline Function

    You can pass any callable with signature `(x, y) -> (x_curve, y_curve)`
    to use a custom fitting function. Here we use `scipy.interpolate.UnivariateSpline`.
    """)
    return


@app.cell
def _(SplineDraw, mo, np):
    from scipy.interpolate import UnivariateSpline

    def fit_spline(x, y):
        order = np.argsort(x)
        spl = UnivariateSpline(x[order], y[order], s=len(x) * 100)
        x_line = np.linspace(x.min(), x.max(), 200)
        return x_line, spl(x_line)

    custom_widget = mo.ui.anywidget(SplineDraw(spline_fn=fit_spline))
    custom_widget
    return UnivariateSpline, custom_widget, fit_spline


@app.cell
def _(custom_widget):
    custom_curves = custom_widget.curve_as_numpy
    total_custom = sum(len(x) for x, y in custom_curves.values())
    f"Custom curve has {total_custom} points, drawn {len(custom_widget.data)} scatter points"
    return (custom_curves, total_custom)


if __name__ == "__main__":
    app.run()
