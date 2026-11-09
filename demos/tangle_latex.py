# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.23.3",
#     "wigglystuff==0.5.37",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import math

    import marimo as mo

    from wigglystuff import ObservablePlot, TangleLatex

    return ObservablePlot, TangleLatex, math, mo


@app.cell(hide_code=True)
def _(mo):
    theme = mo.ui.dropdown(
        options=["auto", "light", "dark"], value="light", label="Widget theme"
    )
    mo.vstack(
        [
            mo.md(r"""
            # Tangle parameters in LaTeX

            Drag any colored value horizontally. Click it to type an exact value,
            and use **Reset** to return to the values declared in Python.
            """),
            theme,
        ],
        gap=0.5,
    )
    return (theme,)


@app.cell(hide_code=True)
def _(TangleLatex, mo, theme):
    numbers = mo.ui.anywidget(
        TangleLatex(
            latex=r"y = \note{bend}{\tangle{a}}x^2 + \tangle{b}x + \tangle{c}",
            parameters={
                "a": {
                    "value": 1.5,
                    "min_value": -5,
                    "max_value": 5,
                    "step": 0.1,
                    "digits": 1,
                    "color": {"light": "#246bce", "dark": "#75a7ff"},
                },
                "b": {
                    "value": -2,
                    "min_value": -10,
                    "max_value": 10,
                    "step": 0.5,
                    "digits": 1,
                    "color": {"light": "#b45b1b", "dark": "#ffad66"},
                },
                "c": {
                    "value": 0.5,
                    "min_value": -5,
                    "max_value": 5,
                    "step": 0.1,
                    "digits": 1,
                    "color": {"light": "#147a68", "dark": "#5ed5bd"},
                },
            },
            notes={"bend": "how sharply it bends; below $0$ flips it"},
            theme=theme.value,
        )
    )
    return (numbers,)


@app.cell(hide_code=True)
def _(ObservablePlot, mo, numbers):
    a, b, c = numbers.values["a"], numbers.values["b"], numbers.values["c"]
    # committed_values holds the values from before the current drag.
    a0, b0, c0 = (numbers.committed_values[k] for k in "abc")
    _xs = [-5 + i * 10 / 200 for i in range(201)]
    curve = [{"x": x, "y": a * x**2 + b * x + c} for x in _xs]
    _reference = [{"x": x, "y": a0 * x**2 + b0 * x + c0} for x in _xs]
    parabola = ObservablePlot(
        """
        Plot.plot({
            y: { grid: true },
            marks: [
                Plot.ruleY([0]),
                Plot.ruleX([0]),
                Plot.line(reference, { x: "x", y: "y", stroke: "#246bce", strokeDasharray: "4,4" }),
                Plot.line(curve, { x: "x", y: "y", stroke: "#246bce", strokeWidth: 2 }),
            ],
        })
        """,
        variables={"curve": curve, "reference": _reference},
        width=420,
        height=300,
    )
    mo.hstack(
        [
            parabola,
            mo.vstack(
                [
                    mo.md("### Numbers in the formula"),
                    numbers,
                    mo.md(f"Current values: `{numbers.values}`"),
                    mo.md("While you drag, `values` follows along and `committed_values` keeps the numbers from before the drag, drawn as the dashed line."),
                ],
                gap=0.5,
            ),
        ],
        align="center",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _(TangleLatex, mo, theme):
    symbols = mo.ui.anywidget(
        TangleLatex(
            latex=(
                r"p(x) = \note{norm}{\frac{1}{\tangle{sigma}\sqrt{2\pi}}}"
                r"\exp\!\left(-\frac{(x-\note{center}{\tangle{mu}})^2}"
                r"{2\note{width}{\tangle{sigma}}^2}\right)"
            ),
            parameters={
                "mu": {
                    "value": 0,
                    "min_value": -4,
                    "max_value": 4,
                    "step": 0.1,
                    "digits": 1,
                    "display": "symbol",
                    "symbol": r"\mu",
                    "label": "mean",
                    "color": {"light": "#a23b78", "dark": "#f08bc2"},
                },
                "sigma": {
                    "value": 1,
                    "min_value": 0.1,
                    "max_value": 4,
                    "step": 0.1,
                    "digits": 1,
                    "display": "symbol",
                    "symbol": r"\sigma",
                    "label": "standard deviation",
                    "color": {"light": "#6f5cbd", "dark": "#b9a8ff"},
                },
            },
            notes={
                "norm": "keeps the area under the curve at $1$",
                "center": "**mean**: where the bell is centered",
                "width": "**standard deviation**: how wide the bell is",
            },
            reveal_all_on_drag=False,
            editor="inline",
            theme=theme.value,
        )
    )
    return (symbols,)


@app.cell(hide_code=True)
def _(ObservablePlot, math, mo, symbols):
    def _normal(x, mu, sigma):
        return math.exp(-((x - mu) ** 2) / (2 * sigma**2)) / (
            sigma * math.sqrt(2 * math.pi)
        )

    mu, sigma = symbols.values["mu"], symbols.values["sigma"]
    mu0, sigma0 = symbols.committed_values["mu"], symbols.committed_values["sigma"]
    _xs = [-6 + i * 12 / 200 for i in range(201)]
    pdf = [{"x": x, "y": _normal(x, mu, sigma)} for x in _xs]
    _reference = [{"x": x, "y": _normal(x, mu0, sigma0)} for x in _xs]
    bell = ObservablePlot(
        """
        Plot.plot({
            y: { grid: true },
            marks: [
                Plot.ruleY([0]),
                Plot.line(reference, { x: "x", y: "y", stroke: "#a23b78", strokeDasharray: "4,4" }),
                Plot.areaY(pdf, { x: "x", y: "y", fill: "#a23b78", fillOpacity: 0.15 }),
                Plot.line(pdf, { x: "x", y: "y", stroke: "#a23b78", strokeWidth: 2 }),
            ],
        })
        """,
        variables={"pdf": pdf, "reference": _reference},
        width=420,
        height=300,
    )
    mo.hstack(
        [
            bell,
            mo.vstack(
                [
                    mo.md("### Symbols that reveal together while dragging"),
                    symbols,
                    mo.md(f"Current values: `{symbols.values}`"),
                    mo.md("While you drag, `values` follows along and `committed_values` keeps the numbers from before the drag, drawn as the dashed line."),
                ],
                gap=0.5,
            ),
        ],
        align="center",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Old and new values

    Next to `values`, a `TangleLatex` also stores `committed_values`. While you
    drag, `values` follows the pointer and `committed_values` keeps the numbers
    from before the drag. When you let go, the two match again. Drag a number
    below and watch the rows split.
    """)
    return


@app.cell
def _(TangleLatex, mo, theme):
    line = mo.ui.anywidget(
        TangleLatex(
            latex=r"y = \tangle{m}x + \tangle{c}",
            parameters={
                "m": {"value": 2, "min_value": -10, "max_value": 10, "step": 0.5},
                "c": {"value": 1, "min_value": -10, "max_value": 10, "step": 0.5},
            },
            theme=theme.value,
        )
    )
    return (line,)


@app.cell(hide_code=True)
def _(line, mo):
    mo.vstack(
        [
            line,
            mo.md(f"""
    | | `m` | `c` |
    | --- | --- | --- |
    | `values` | {line.values["m"]:g} | {line.values["c"]:g} |
    | `committed_values` | {line.committed_values["m"]:g} | {line.committed_values["c"]:g} |
    """),
        ],
        gap=1,
    )
    return


if __name__ == "__main__":
    app.run()
