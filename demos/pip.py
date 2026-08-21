# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.27",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Pip

    `Pip` wraps a widget and adds a button that moves it into a window floating
    above everything else — the browser's
    [Document Picture-in-Picture API](https://developer.mozilla.org/en-US/docs/Web/API/Document_Picture-in-Picture_API),
    the feature that keeps a video above other applications, holding a live widget
    instead of a video. Chromium and Firefox only.

    Pop the chart out, then sweep the sliders below it. Each move adds a point, so
    the floating chart draws a resonance curve as you go, and stays in view however
    far you scroll from the sliders.
    """)
    return


@app.cell
def _():
    from wigglystuff import Pip, ScatterLog

    log = ScatterLog(
        x_label="frequency ratio",
        y_label="response",
        color_label="damping",
        max_points=400,
    )
    # The window is the chart plus its axes, labels and legend.
    Pip(log, width=560, height=420)
    return (log,)


@app.cell(hide_code=True)
def _(mo):
    freq = mo.ui.slider(0.1, 2.5, step=0.05, value=0.4, label="frequency ratio")
    damping = mo.ui.slider(0.05, 0.8, step=0.05, value=0.2, label="damping")
    mo.hstack([freq, damping], justify="start", gap=2)
    return damping, freq


@app.cell(hide_code=True)
def _(damping, freq, log, math, mo):
    # Re-runs on every slider move; each run adds a point to the chart above.
    response = 1 / math.sqrt(
        (1 - freq.value**2) ** 2 + (2 * damping.value * freq.value) ** 2
    )
    log.append(freq.value, response, color=f"{damping.value:.2f}")
    mo.md(f"response at {freq.value:.2f} is `{response:.2f}`")
    return


@app.cell
def _():
    import math

    import marimo as mo

    return math, mo


if __name__ == "__main__":
    app.run()
