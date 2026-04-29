import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import TangleSlider, TangleChoice, TangleSelect

    return TangleChoice, TangleSelect, TangleSlider, mo


@app.cell
def _(TangleSlider, mo):
    coffees = mo.ui.anywidget(TangleSlider(amount=10, min_value=0, max_value=100, step=1, suffix=" coffees", digits=0))
    coffees
    return


@app.cell
def _(TangleChoice, mo):
    emoji = mo.ui.anywidget(TangleChoice(choices=["smile", "party", "boom"]))
    emoji
    return


@app.cell
def _(TangleSelect, mo):
    veggie = mo.ui.anywidget(TangleSelect(choices=["potato", "carrot", "apple"]))
    veggie
    return


if __name__ == "__main__":
    app.run()
