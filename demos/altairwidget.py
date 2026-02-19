import marimo

__generated_with = "0.19.11"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    from wigglystuff import AltairWidget

    widget = AltairWidget(width=500, height=400)
    return (widget,)


@app.cell
def _(mo, widget):
    wrapped = mo.ui.anywidget(widget)
    return (wrapped,)


@app.cell
def _(mo):
    phase = mo.ui.slider(0, 6.28, value=0, step=0.1, label="Phase")
    amplitude = mo.ui.slider(0.1, 2.0, value=1.0, step=0.1, label="Amplitude")
    mo.hstack([phase, amplitude])
    return amplitude, phase


@app.cell
def _(amplitude, phase, widget):
    import altair as alt
    import numpy as np
    import pandas as pd

    x = np.linspace(0, 4 * np.pi, 80)
    y = amplitude.value * np.sin(x + phase.value)

    df = pd.DataFrame({"x": x, "y": y})

    chart = (
        alt.Chart(df)
        .mark_circle(size=60)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 4 * np.pi])),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-2.5, 2.5])),
        )
        .properties(width=500, height=400)
        .interactive()
    )

    widget.chart = chart
    return


@app.cell
def _(wrapped):
    wrapped
    return


if __name__ == "__main__":
    app.run()
