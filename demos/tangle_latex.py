# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.23.3",
#     "wigglystuff==0.5.20",
# ]
# ///

import marimo

__generated_with = "0.23.3"
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
            latex=r"y = \tangle{a}x^2 + \tangle{b}x + \tangle{c}",
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
            theme=theme.value,
        )
    )
    return (numbers,)


@app.cell(hide_code=True)
def _(ObservablePlot, mo, numbers):
    a, b, c = numbers.values["a"], numbers.values["b"], numbers.values["c"]
    a0 = numbers.parameters["a"]["value"]
    b0 = numbers.parameters["b"]["value"]
    c0 = numbers.parameters["c"]["value"]
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
                Plot.line(reference, { x: "x", y: "y", stroke: "#9ca3af", strokeDasharray: "4,4" }),
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
                    mo.md("The dashed grey line is the original curve."),
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
                r"p(x) = \frac{1}{\tangle{sigma}\sqrt{2\pi}}"
                r"\exp\!\left(-\frac{(x-\tangle{mu})^2}"
                r"{2\tangle{sigma}^2}\right)"
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
    mu0 = symbols.parameters["mu"]["value"]
    sigma0 = symbols.parameters["sigma"]["value"]
    _xs = [-6 + i * 12 / 200 for i in range(201)]
    pdf = [{"x": x, "y": _normal(x, mu, sigma)} for x in _xs]
    _reference = [{"x": x, "y": _normal(x, mu0, sigma0)} for x in _xs]
    bell = ObservablePlot(
        """
        Plot.plot({
            y: { grid: true },
            marks: [
                Plot.ruleY([0]),
                Plot.line(reference, { x: "x", y: "y", stroke: "#9ca3af", strokeDasharray: "4,4" }),
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
                    mo.md("The dashed grey line is the original distribution."),
                ],
                gap=0.5,
            ),
        ],
        align="center",
        gap=2,
    )
    return


if __name__ == "__main__":
    app.run()
