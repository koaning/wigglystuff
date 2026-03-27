# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "scikit-learn",
#     "wigglystuff==0.3.1",
# ]
# ///
import marimo

__generated_with = "0.20.2"
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
    You just need to pass a callable `(x, y) -> (x_curve, y_curve)`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Scikit-Learn Pipeline

    Use a scikit-learn pipeline to fit a spline through the drawn points.
    The pipeline is reusable: after drawing, you can call `pipe.predict()`
    on new data outside the widget.
    """)
    return


@app.cell
def _(mo, np):
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import SplineTransformer

    from wigglystuff import SplineDraw

    pipe = make_pipeline(SplineTransformer(), LinearRegression())

    def sklearn_spline(x, y):
        pipe.fit(x.reshape(-1, 1), y)
        x_curve = np.linspace(x.min() - 300 , x.max() + 300, 1000)
        return x_curve, pipe.predict(x_curve.reshape(-1, 1))

    sklearn_widget = mo.ui.anywidget(SplineDraw(spline_fn=sklearn_spline))
    sklearn_widget
    return SplineDraw, pipe, sklearn_widget


@app.cell
def _(mo, np, pipe, sklearn_widget):
    _msg = "Draw at least 2 points to see predictions on new data"
    if len(sklearn_widget.data) >= 2:
        x_new = np.array([100, 200, 300, 400, 500]).reshape(-1, 1)
        preds = pipe.predict(x_new)
        _msg = f"Predictions on new x-values: {np.round(preds, 1)}"
    mo.md(_msg)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Swapping the spline function with `redraw()`

    Use `widget.redraw()` to recompute the curve when external state changes,
    or pass a new callable to swap the fitting function entirely.
    """)
    return


@app.cell
def _(np):
    from sklearn.kernel_ridge import KernelRidge as _KR

    def make_kernel_fn(gamma):
        def fn(x, y):
            kr = _KR(kernel="rbf", gamma=gamma)
            kr.fit(x.reshape(-1, 1), y)
            x_curve = np.linspace(x.min(), x.max(), 200)
            return x_curve, kr.predict(x_curve.reshape(-1, 1))
        return fn

    return (make_kernel_fn,)


@app.cell
def _(mo):
    gamma_slider = mo.ui.slider(
        start=-6, stop=0, step=0.5, value=-4, label="log10(gamma)"
    )
    return (gamma_slider,)


@app.cell
def _(SplineDraw, make_kernel_fn, mo):
    redraw_widget = mo.ui.anywidget(
        SplineDraw(spline_fn=make_kernel_fn(10 ** (-4)))
    )
    return (redraw_widget,)


@app.cell
def _(gamma_slider, mo, redraw_widget):
    mo.vstack([gamma_slider, redraw_widget])
    return


@app.cell
def _(gamma_slider, make_kernel_fn, redraw_widget):
    redraw_widget.widget.redraw(spline_fn=make_kernel_fn(10 ** gamma_slider.value))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Multiple Classes

    With `n_classes > 1`, each class gets its own independent spline curve
    drawn in the matching color. Try drawing points with different classes.
    """)
    return


@app.cell
def _(SplineDraw, mo, np):
    from sklearn.kernel_ridge import KernelRidge

    def kernel_smooth(x, y):
        kr = KernelRidge(kernel="rbf", gamma=0.0001)
        kr.fit(x.reshape(-1, 1), y)
        x_curve = np.linspace(x.min(), x.max(), 200)
        return x_curve, kr.predict(x_curve.reshape(-1, 1))

    multi_widget = mo.ui.anywidget(SplineDraw(spline_fn=kernel_smooth, n_classes=2))
    multi_widget
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_curves = multi_widget.curve_as_numpy
    info = ", ".join(f"{c}: {len(x)} pts" for c, (x, y) in multi_curves.items())
    info if info else "Draw some points to see curves"
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Drawing a Distribution

    A step-function interpolation produces a histogram-like curve.
    Paint points to sketch a distribution shape, then sample from it.
    """)
    return


@app.cell
def _(SplineDraw, mo, np):
    def step_interpolate(x, y, n_bins=20):
        edges = np.linspace(x.min(), x.max(), n_bins + 1)
        bin_idx = np.clip(np.digitize(x, edges) - 1, 0, n_bins - 1)
        x_out, y_out = [], []
        for i in range(n_bins):
            mask = bin_idx == i
            val = float(np.mean(y[mask])) if mask.any() else 0.0
            x_out.extend([float(edges[i]), float(edges[i + 1])])
            y_out.extend([val, val])
        return np.array(x_out), np.array(y_out)

    hist_widget = mo.ui.anywidget(SplineDraw(spline_fn=step_interpolate))
    hist_widget
    return (hist_widget,)


@app.cell
def _(hist_widget, np):
    import matplotlib.pylab as plt

    _msg = "Draw at least 2 points to define a distribution"
    if len(hist_widget.data) >= 2:
        _curves = hist_widget.curve_as_numpy
        if _curves:
            _x_curve, _y_curve = list(_curves.values())[0]
            _density = np.maximum(_y_curve, 0)
            if _density.sum() > 0:
                _density /= _density.sum()
                _samples = np.random.choice(_x_curve, size=5000, p=_density)
                _msg = f"Sampled 500 points — mean: {_samples.mean():.1f}, std: {_samples.std():.1f}"
            else:
                _msg = "Draw points above the x-axis to define a distribution"

    plt.hist(_samples, bins=20);
    plt.show()
    return


if __name__ == "__main__":
    app.run()
