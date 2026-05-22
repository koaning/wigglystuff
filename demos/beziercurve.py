import marimo

__generated_with = "0.23.6"
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
    """)
    return


@app.cell
def _(curve):
    curve
    return


@app.cell
def _(curve, mo):
    mo.callout(
        f"t = {curve.t:.3f}; current point = ({curve.x:.3f}, {curve.y:.3f}); "
        f"{len(curve.points)} control points"
    )
    return


if __name__ == "__main__":
    app.run()
