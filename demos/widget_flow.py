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

    Live widgets laid out as a top-to-bottom DAG, in the style of `FormulaDAG`.
    Hover a caption to trace a node's ancestry, click it to pin, fold a card to
    its caption, or flip the direction from the toolbar.
    """)
    return


@app.cell
def _(mo):
    n_points = mo.ui.slider(10, 200, value=60, step=10, label="points", show_value=True)
    noise = mo.ui.slider(0.0, 1.0, value=0.25, step=0.05, label="noise", show_value=True)
    seed = mo.ui.number(0, 100, value=7, label="seed")
    degree = mo.ui.slider(1, 12, value=3, label="degree", show_value=True)
    return degree, n_points, noise, seed


@app.cell
def _(alt, n_points, noise, np, pd, seed):
    _rng = np.random.default_rng(seed.value)
    _x = np.sort(_rng.uniform(0, 6, n_points.value))
    df = pd.DataFrame({"x": _x, "y": np.sin(_x) + _rng.normal(0, noise.value, len(_x))})
    data_chart = (
        alt.Chart(df)
        .mark_circle(size=28, color="#5b4fbf", opacity=0.75)
        .encode(x=alt.X("x", title=None), y=alt.Y("y", title=None))
        .properties(width=230, height=140)
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
    ).properties(width=230, height=140).configure(background="transparent").configure_view(strokeWidth=0)
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


@app.cell
def _(
    WidgetFlow,
    data_chart,
    degree,
    fit_chart,
    mo,
    n_points,
    noise,
    score,
    seed,
):
    default_edges = [
        ("n_points", "data"),
        ("noise", "data"),
        ("seed", "data"),
        ("data", "fit", "x, y"),
        ("degree", "fit"),
        ("fit", "score", "residuals"),
    ]

    def build(edges=default_edges, **kwargs):
        return WidgetFlow(
            nodes={
                "n_points": n_points,
                "noise": noise,
                "seed": seed,
                "data": data_chart,
                "degree": degree,
                "fit": fit_chart,
                "score": score,
            },
            edges=edges,
            labels={"data": "sample", "fit": "polyfit"},
            notes={
                "noise": "std of the gaussian noise on $\\sin(x)$",
                "degree": "too high and the curve starts chasing noise",
            },
            groups={"inputs": ["n_points", "noise", "seed"]},
            **kwargs,
        )

    build()
    return (build,)


@app.cell
def _(build):
    build(direction="right", collapsed=["seed"])
    return


@app.cell
def _(WidgetFlow, degree, fit_chart, noise):
    # beside= puts an input on the same row as the node it feeds, so its arrow
    # comes straight in from the left or right instead of from above.
    WidgetFlow(
        nodes={"noise": noise, "degree": degree, "fit": fit_chart},
        edges=[("noise", "fit", "σ"), ("degree", "fit", "k")],
        beside={"noise": ("fit", "left"), "degree": ("fit", "right")},
        labels={"fit": "polyfit"},
        color_by="none",
    )
    return


@app.cell
def _(build):
    # color_by="none" draws every arrow in one ink; colors= or an edge's
    # "color" picks out the ones you care about.
    build(
        edges=[
            ("n_points", "data"),
            ("noise", "data"),
            ("seed", "data", {"enter": "right"}),
            ("data", "fit", "x, y"),
            ("degree", "fit", {"color": "#c2410c"}),
            ("fit", "score", "residuals"),
        ],
        beside={"degree": ("fit", "right")},
        color_by="none",
    )
    return


if __name__ == "__main__":
    app.run()
