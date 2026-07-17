import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import TangleLatex

    return TangleLatex, mo


@app.cell
def _(TangleLatex, mo):
    numeric = mo.ui.anywidget(
        TangleLatex(
            latex=r"y = \tangle{a}x + \tangle{b}",
            parameters={
                "a": {
                    "value": 2.5,
                    "min_value": -5,
                    "max_value": 5,
                    "step": 0.1,
                    "digits": 1,
                    "display": "number",
                    "color": {"light": "#246bce", "dark": "#75a7ff"},
                },
                "b": {
                    "value": 1,
                    "min_value": -10,
                    "max_value": 10,
                    "step": 0.5,
                    "digits": 1,
                    "display": "number",
                    "color": {"light": "#b45b1b", "dark": "#ffad66"},
                },
            },
            theme="dark",
        )
    )
    numeric
    return (numeric,)


@app.cell
def _(TangleLatex, mo):
    selected_only = mo.ui.anywidget(
        TangleLatex(
            latex=r"f(x) = \frac{1}{\tangle{a}} + \tangle{b}x + \tangle{a}",
            parameters={
                "a": {"value": 2.5, "display": "symbol", "step": 0.1},
                "b": {"value": 1, "display": "symbol", "step": 0.5},
            },
            reveal_all_on_drag=False,
            editor="inline",
            theme="light",
        )
    )
    selected_only
    return (selected_only,)


@app.cell
def _(TangleLatex, mo):
    reveal_all = mo.ui.anywidget(
        TangleLatex(
            latex=r"g(x) = \frac{1}{\tangle{a}} + \tangle{b}x + \tangle{a}",
            parameters={
                "a": {"value": 2.5, "display": "symbol", "step": 0.1},
                "b": {"value": 1, "display": "symbol", "step": 0.5},
            },
            reveal_all_on_drag=True,
        )
    )
    reveal_all
    return (reveal_all,)


@app.cell
def _(mo, numeric, reveal_all, selected_only):
    mo.md(f"""
    numeric={numeric.values}; selected={selected_only.values}; all={reveal_all.values}
    """)
    return


if __name__ == "__main__":
    app.run()
