# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pandas",
#     "wigglystuff==0.5.17",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from wigglystuff import ObservablePlot

    return ObservablePlot, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ObservablePlot

    `ObservablePlot` runs [Observable Plot](https://observablehq.com/plot/) code
    directly in the notebook. Plot (and d3) are loaded from a CDN and your
    JavaScript is evaluated the way an Observable cell would be: as an expression
    that returns a DOM node (a bare `Plot.plot({...})`).

    Python data is injected by name through `variables`, so a DataFrame passed as
    `{"vacancies": df}` can be referenced as `vacancies` inside the code. Pandas /
    polars DataFrames and numpy arrays are converted to JSON records/lists for you.
    """)
    return


@app.cell
def _(mo):
    slider = mo.ui.slider(1, 10, 1, label="final variable")
    slider
    return (slider,)


@app.cell
def _(pd, slider):
    vacancies = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "vacancies": [3, 5, 2, 8, 6, slider.value],
        }
    )
    return (vacancies,)


@app.cell
def _(ObservablePlot, vacancies):
    bars = """
        Plot.plot({
            height: 260,
            // Ordinal x defaults to sorting the domain (so months would come
            // out alphabetically); pin the domain to keep calendar order.
            x: { domain: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] },
            marks: [
                Plot.barY(vacancies, { x: "month", y: "vacancies", fill: "#4f46e5" }),
                Plot.ruleY([0]),
            ],
        })
    """

    ObservablePlot(bars, variables={"vacancies": vacancies}, width=520)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Any JSON-able variable works

    You are not limited to DataFrames — a plain list of dicts is injected just the
    same. `d3` is in scope too, handy for scales, ranges, and helpers.
    """)
    return


@app.cell
def _(mo):
    n_slider = mo.ui.slider(10, 100, 1, label="number of points")
    n_slider
    return (n_slider,)


@app.cell
def _(ObservablePlot, n_slider, pd):
    points = pd.DataFrame([
        {"x": i, "y": (i * 7 % 11), "g": "even" if i % 2 == 0 else "odd"}
        for i in range(n_slider.value)
    ])

    scatter = """
        Plot.plot({
            grid: true,
            color: { legend: true },
            marks: [ Plot.dot(points, { x: "x", y: "y", stroke: "g", r: 4 }) ],
        })
    """

    ObservablePlot(scatter, variables={"points": points}, width=520)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Window reducers

    A faithful take on Observable's
    [window reducers](https://observablehq.com/@observablehq/plot-window-reduce)
    example: a noisy daily series (a random walk built in numpy) with a rolling
    mean layered on top via `Plot.windowY`. Drag the slider to set the window
    size — it is injected as the variable `k`, so the chart re-renders live. The
    dates are handed over as epoch-milliseconds and read back as a UTC axis.
    """)
    return


@app.cell
def _(mo):
    window_size = mo.ui.slider(2, 60, 1, value=20, label="window size (days)")
    window_size
    return (window_size,)


@app.cell
def _(np, pd):
    _rng = np.random.default_rng(42)
    _n = 400
    _dates = pd.date_range("2023-01-01", periods=_n, freq="D")
    series = pd.DataFrame(
        {
            # epoch ms -> Plot reads these as dates under an x scale of type "utc"
            "date": _dates.astype("int64") // 10**6,
            "value": (100 + np.cumsum(_rng.normal(0.05, 1.0, _n))).round(2),
        }
    )
    return (series,)


@app.cell
def _(ObservablePlot, series, window_size):
    window = """
        Plot.plot({
            height: 300,
            y: { grid: true, label: "price ($)" },
            x: { type: "utc", label: null },
            marks: [
                Plot.lineY(series, { x: "date", y: "value", stroke: "#cbd5e1" }),
                Plot.lineY(series, Plot.windowY({ k: k, reduce: "mean" },
                    { x: "date", y: "value", stroke: "#ef4444", strokeWidth: 2 })),
            ],
        })
    """

    ObservablePlot(
        window,
        variables={"series": series, "k": window_size.value},
        width=680,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## PSR B1919+21 — the "Joy Division" pulsar

    A tribute to Observable's
    [PSR B1919+21](https://observablehq.com/@observablehq/plot-psr-b1919-21) —
    black lines on white, like the OG demo. Each of the 80 rows is one pulse
    period, generated in numpy and injected as a long-form list of
    `{row, t, value}`. We use `d3.groups` to build one area + line mark **per
    row** in back-to-front order, giving each row a small vertical offset; the
    white area fills occlude the rows behind, so ridges overlap cleanly without
    lines bleeding through.
    """)
    return


@app.cell
def _(mo):
    rows_slider = mo.ui.slider(40, 100, 1, label="rows")
    rows_slider
    return (rows_slider,)


@app.cell
def _(ObservablePlot, joy, pulses):
    ObservablePlot(joy, variables={"pulses": pulses}, width=580, height=780)
    return


@app.cell(hide_code=True)
def _(np, rows_slider):
    _rng = np.random.default_rng(7)
    _rows, _cols = rows_slider.value, 220
    _x = np.linspace(-3, 3, _cols)
    pulses = []
    for _r in range(_rows):
        _center = 0.35 * np.sin(_r / 6) + _rng.normal(0, 0.15)
        _amp = 1.0 + 0.8 * np.exp(-((_r - 40) ** 2) / 300) + _rng.normal(0, 0.05)
        _y = _amp * np.exp(-((_x - _center) ** 2) / 0.12) + _rng.normal(0, 0.07, _cols)
        _y = np.clip(_y, 0, None)
        for _c in range(_cols):
            pulses.append({"row": _r, "t": float(_x[_c]), "value": float(_y[_c])})
    return (pulses,)


@app.cell
def _():
    joy = """
        Plot.plot({
            width: 560,
            height: 760,
            marginTop: 30,
            marginBottom: 30,
            x: { axis: null },
            y: { axis: null },
            // One area + line per row, drawn back (row 0) to front. Each row sits
            // `step` px lower; pulses rise by `amp`, so they overlap. The white
            // area fill hides the rows behind, so nothing bleeds through.
            marks: d3.groups(pulses, (d) => d.row)
                .sort((a, b) => d3.ascending(a[0], b[0]))
                .flatMap(([row, data]) => {
                    const step = 8;
                    const amp = 26;
                    const base = -row * step;
                    const top = (d) => base + d.value * amp;
                    return [
                        Plot.areaY(data, { x: "t", y1: () => base, y2: top, fill: "white", curve: "basis" }),
                        Plot.lineY(data, { x: "t", y: top, stroke: "black", strokeWidth: 1, curve: "basis" }),
                    ];
                }),
        })
    """
    return (joy,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Loading from a file or URL

    The first argument also accepts a path to a `.js` file or an `http(s)://`
    URL — the source is fetched in Python, so the browser always gets plain JS.
    Reassigning `widget.code` or `widget.variables` re-renders the chart.
    """)
    return


if __name__ == "__main__":
    app.run()
