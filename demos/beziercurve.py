# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.3",
# ]
# ///
import marimo

__generated_with = "0.23.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import BezierCurve

    curve = mo.ui.anywidget(
        BezierCurve(
            closed=False,
            loop=False,
            width=340,
            height=340,
            duration_ms=12000,
            show_axes=True,
            x_bounds=(-2.0, 2.0),
            y_bounds=(0.0, 10.0),
            points=[
                {"x": -1.5, "y": 2.0},
                {"x": -0.5, "y": 8.5},
                {"x": 0.8, "y": 8.5},
                {"x": 1.6, "y": 2.0},
            ],
            n_samples=80,
        )
    )
    return curve, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## BezierCurve

    Drag the control points, double-click the canvas to add another point,
    double-click a point to remove it, and use the checkboxes to close the
    curve or loop playback.

    This demo opts into the **axes** (`show_axes=True`) so the configured
    `x_bounds=(-2, 2)` and `y_bounds=(0, 10)` are visible as tick labels.
    It also requests `n_samples=80` densely sampled points along the
    rendered curve — those are synced back into Python on the `samples`
    traitlet, so you can iterate over the whole curve below.
    """)
    return


@app.cell
def _(curve):
    curve
    return


@app.cell(hide_code=True)
def _(curve, mo):
    first = curve.samples[0] if curve.samples else {"x": float("nan"), "y": float("nan")}
    last = curve.samples[-1] if curve.samples else {"x": float("nan"), "y": float("nan")}
    mo.callout(
        f"t = {curve.t:.3f}; current point = ({curve.x:.3f}, {curve.y:.3f}); "
        f"{len(curve.points)} control points; {len(curve.samples)} samples "
        f"(first = ({first['x']:.2f}, {first['y']:.2f}), "
        f"last = ({last['x']:.2f}, {last['y']:.2f}))"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Looping over `samples` in Python

    Now that the browser pushes every sampled `(x, y)` pair to Python on
    the `samples` traitlet, you can compute things over the whole curve in
    bulk. Drag a control point and watch the arc-length update live.
    """)
    return


@app.cell
def _(curve, mo):
    pairs = list(zip(curve.samples, curve.samples[1:]))
    arc_length = sum(
        ((b["x"] - a["x"]) ** 2 + (b["y"] - a["y"]) ** 2) ** 0.5
        for a, b in pairs
    )
    preview = ", ".join(
        f"({p['x']:.2f}, {p['y']:.2f})" for p in curve.samples[:3]
    )
    mo.md(f"""
    - Approximate arc length from `samples`: **{arc_length:.3f}**
    - First three samples: `{preview}`
    - `len(curve.samples) == {len(curve.samples)}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Going further with numpy

    `samples` gives you a finite number of `(x, y)` pairs along the curve.
    If you need values at arbitrary `x` positions in between — for example
    to evaluate the curve on the same grid as some other data — you can
    interpolate from those samples with numpy:

    ```python
    import numpy as np

    xs = np.array([p["x"] for p in curve.samples])
    ys = np.array([p["y"] for p in curve.samples])

    # Sort by x for monotonic interpolation, then evaluate on a finer grid.
    order = np.argsort(xs)
    finer_x = np.linspace(xs[order].min(), xs[order].max(), 1000)
    finer_y = np.interp(finer_x, xs[order], ys[order])
    ```

    `np.interp` does piecewise-linear interpolation between the rendered
    samples, so accuracy improves as you raise `n_samples`. For smoother
    interpolation between samples (e.g. cubic), reach for
    `scipy.interpolate.CubicSpline` instead.
    """)
    return


if __name__ == "__main__":
    app.run()
