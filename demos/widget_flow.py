# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "altair",
#     "marimo",
#     "numpy",
#     "pandas",
#     "wigglystuff==0.5.40",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    import altair as alt
    import numpy as np
    import pandas as pd

    from wigglystuff.widget_flow import WidgetFlow

    return WidgetFlow, alt, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # WidgetFlow

    Live widgets laid out as a DAG, in the style of `FormulaDAG`. The quickest
    way in is `WidgetFlow.from_widgets([...])`: pass the widgets, and the
    arrows come from marimo's own dataflow graph while every widget is
    captioned with its variable name.
    """)
    return


@app.cell
def _(mo):
    n_points = mo.ui.slider(10, 200, value=60, step=10, label="points", show_value=True)
    noise = mo.ui.slider(0.0, 1.0, value=0.25, step=0.05, label="noise", show_value=True)
    seed = mo.ui.number(0, 100, value=7, label="seed")
    return n_points, noise, seed


@app.cell
def _(mo):
    degree = mo.ui.slider(1, 12, value=3, label="degree", show_value=True)
    return (degree,)


@app.cell
def _(alt, n_points, noise, np, pd, seed):
    _rng = np.random.default_rng(seed.value)
    _x = np.sort(_rng.uniform(0, 6, n_points.value))
    df = pd.DataFrame({"x": _x, "y": np.sin(_x) + _rng.normal(0, noise.value, len(_x))})
    data_chart = (
        alt.Chart(df)
        .mark_circle(size=28, color="#5b4fbf", opacity=0.75)
        .encode(x=alt.X("x", title=None), y=alt.Y("y", title=None))
        .properties(width=230, height=140, usermeta={"embedOptions": {"actions": False}})
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
    )
    return data_chart, df


@app.cell
def _(alt, degree, df, np, pd):
    _coef = np.polyfit(df.x, df.y, degree.value)
    _grid = np.linspace(df.x.min(), df.x.max(), 200)
    fit_df = pd.DataFrame({"x": _grid, "y": np.polyval(_coef, _grid)})
    residuals = df.y - np.polyval(_coef, df.x)
    fit_chart = (
        alt.Chart(df).mark_circle(size=18, color="#999", opacity=0.5).encode(x=alt.X("x", title=None), y=alt.Y("y", title=None))
        + alt.Chart(fit_df).mark_line(color="#b3262e", strokeWidth=2).encode(x="x", y="y")
    ).properties(width=230, height=140, usermeta={"embedOptions": {"actions": False}}).configure(background="transparent").configure_view(strokeWidth=0)
    return fit_chart, residuals


@app.cell
def _(mo, np, residuals):
    score = mo.stat(
        value=f"{float(np.sqrt(np.mean(residuals**2))):.3f}",
        label="RMSE",
        caption="in-sample",
        bordered=False,
    )
    return (score,)


@app.cell(expand_output=True)
def _(WidgetFlow, data_chart, degree, fit_chart, n_points, noise, score, seed):
    WidgetFlow.from_widgets(
        [n_points, noise, seed, data_chart, degree, fit_chart, score],
        notes=[
            (noise, "std of the gaussian noise on $\\sin(x)$"),
            (degree, "too high and the curve starts chasing noise"),
        ],
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    `direction="right"` lays the layers out left to right instead.
    """)
    return


@app.cell(expand_output=True)
def _(WidgetFlow, data_chart, degree, fit_chart, n_points, noise, score, seed):
    WidgetFlow.from_widgets(
        [n_points, noise, seed, data_chart, degree, fit_chart, score],
        direction="right",
        notes=[(degree, "too high and the curve starts chasing noise")],
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Pass `edges` to `WidgetFlow` yourself to pick the arrows. An edge's third
    item is a label, or a dict with `label`, `color`, `dashed`, and
    `exit`/`enter` sides. `layers` pushes a widget further down: here `degree`
    sits next to the data it is fitted to instead of at the top.
    """)
    return


@app.cell(expand_output=True)
def _(WidgetFlow, data_chart, degree, fit_chart, n_points, noise, score, seed):
    WidgetFlow(
        [n_points, noise, seed, data_chart, degree, fit_chart, score],
        edges=[
            (n_points, data_chart, "n"),
            (noise, data_chart, "σ"),
            (seed, data_chart, {"dashed": True}),
            (data_chart, fit_chart, {"label": "x, y", "color": "#c2410c"}),
            (degree, fit_chart, {"label": "k", "enter": "right"}),
            (fit_chart, score, "residuals"),
        ],
        labels=[(data_chart, "sample"), (fit_chart, "polyfit")],
        layers=[(degree, 1)],
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    `ports` applies the same options to arrows you didn't spell out, such as
    the ones `from_widgets` inferred: here it labels one and pins where
    another lands.
    """)
    return


@app.cell(expand_output=True)
def _(WidgetFlow, data_chart, degree, fit_chart, n_points, noise, score, seed):
    WidgetFlow.from_widgets(
        [n_points, noise, seed, data_chart, degree, fit_chart, score],
        ports=[
            (data_chart, fit_chart, {"label": "x, y"}),
            (degree, fit_chart, {"enter": "top"}),
        ],
        labels=False,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    `align="left"` puts every layer on one grid packed to the left, so the
    first widget of each layer shares a column and the charts line up with
    straight arrows between them. `beside` puts a widget in the same layer as
    another, right after it: here `noise` and `degree` sit next to the chart
    they shape, their arrows running sideways.
    """)
    return


@app.cell(expand_output=True)
def _(WidgetFlow, data_chart, degree, fit_chart, n_points, noise, score):
    WidgetFlow.from_widgets(
        [n_points, noise, data_chart, degree, fit_chart, score],
        align="left",
        beside=[(noise, data_chart), (degree, fit_chart)],
        labels=False,
    )
    return


if __name__ == "__main__":
    app.run()
