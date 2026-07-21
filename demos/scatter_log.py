# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.21",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from wigglystuff import ScatterLog, Slider2D

    return ScatterLog, Slider2D, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ScatterLog

    A widget that **accumulates** points into a live scatter. Drag the 2D
    slider around: every move logs `(x, y)` and the trail builds up. A plain
    marimo state variable can't do this -- reactivity keeps resetting it --
    but the `ScatterLog` instance is stable across re-runs, so it grows a
    history.
    """)
    return


@app.cell
def _(ScatterLog, mo):
    # Create ONCE, in a cell with no dependencies, so it survives re-runs.
    log = mo.ui.anywidget(ScatterLog(x_label="x", y_label="y", max_points=300))
    return (log,)


@app.cell
def _(Slider2D, mo):
    pad = mo.ui.anywidget(Slider2D(width=200, height=200))
    return (pad,)


@app.cell
def _(log, pad):
    [pad, log]
    return


@app.cell
def _(log, pad):
    # Depends on pad, so it re-runs -- and appends -- on every drag.
    quadrant = ("+x" if pad.x >= 0 else "-x") + (" +y" if pad.y >= 0 else " -y")
    log.append(x=pad.x, y=pad.y, color=quadrant)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Points are colored by quadrant, so the legend fills in as you cross the
    axes. `log.data` returns the accumulated points in Python and
    `log.clear()` resets. Because it's just a widget, it drops straight into a
    `WidgetDAG` as a leaf node.
    """)
    return


if __name__ == "__main__":
    app.run()
