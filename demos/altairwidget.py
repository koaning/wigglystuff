# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.19.11",
#     "numpy==2.4.2",
#     "pandas==3.0.1",
#     "wigglystuff==0.2.30",
# ]
# ///

import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    import altair as alt
    import numpy as np
    import pandas as pd

    return alt, np, pd


@app.cell
def _():
    from wigglystuff import AltairWidget

    return (AltairWidget,)


@app.cell
def _(AltairWidget):
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
def _(wrapped):
    wrapped
    return


@app.cell
def _(alt, amplitude, np, pd, phase, widget):
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
def _(mo):
    mo.md("""
    ## Layered chart demo
    """)
    return


@app.cell
def _(AltairWidget):
    layered_widget = AltairWidget(width=500, height=400)
    return (layered_widget,)


@app.cell
def _(layered_widget, mo):
    layered_wrapped = mo.ui.anywidget(layered_widget)
    return (layered_wrapped,)


@app.cell
def _(layered_wrapped):
    layered_wrapped
    return


@app.cell
def _(mo):
    freq = mo.ui.slider(0.5, 3.0, value=1.0, step=0.1, label="Frequency")
    freq
    return (freq,)


@app.cell
def _(alt, freq, layered_widget, np, pd):
    _x = np.linspace(0, 4 * np.pi, 800)
    _df_sin = pd.DataFrame({"x": _x, "y": np.sin(freq.value * _x)})
    _df_cos = pd.DataFrame({"x": _x, "y": np.cos(freq.value * _x)})

    _c1 = (
        alt.Chart(_df_sin)
        .mark_line(color="red")
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 4 * np.pi])),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.5, 1.5])),
        )
    )
    _c2 = (
        alt.Chart(_df_cos)
        .mark_line(color="blue")
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[0, 4 * np.pi])),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.5, 1.5])),
        )
    )

    layered_widget.chart = (_c1 + _c2).properties(width=500, height=400)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
