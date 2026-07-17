# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.23.3",
#     "wigglystuff==0.5.19",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from wigglystuff import TangleLatex

    return TangleLatex, mo


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
def _(mo, numbers):
    mo.vstack(
        [
            mo.md("### Numbers in the formula"),
            numbers,
            mo.md(f"Current values: `{numbers.values}`"),
        ],
        gap=0.5,
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
def _(mo, symbols):
    mo.vstack(
        [
            mo.md("### Symbols that reveal together while dragging"),
            symbols,
            mo.md(f"Current values: `{symbols.values}`"),
        ],
        gap=0.5,
    )
    return


if __name__ == "__main__":
    app.run()
