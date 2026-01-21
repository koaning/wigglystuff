# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.19.4",
#     "numpy==2.4.1",
#     "pandas==2.3.3",
#     "wigglystuff==0.2.14",
# ]
# ///

import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    from wigglystuff import TangleSlider, TangleChoice, TangleSelect
    return TangleChoice, TangleSelect, TangleSlider, alt, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## TangleSlider
    """)
    return


@app.cell
def _(TangleSlider, mo):
    coffees = mo.ui.anywidget(TangleSlider(amount=10, min_value=0, step=1, suffix=" coffees", digits=0))
    price = mo.ui.anywidget(TangleSlider(amount=3.50, min_value=0.01, max_value=10, step=0.01, prefix="$", digits=2))
    return coffees, price


@app.cell
def _(coffees, price):
    total = coffees.amount * price.amount
    return (total,)


@app.cell(hide_code=True)
def _(coffees, mo, price, total):
    mo.md(f"""
    Suppose that you have {coffees} and they each cost {price} then in total you would need to spend ${total:.2f}.
    """)
    return


@app.cell
def _(TangleSlider, mo):
    prob1 = mo.ui.anywidget(TangleSlider(min_value=0, max_value=20, step=0.1, suffix="% of the time", amount=5))
    prob2 = mo.ui.anywidget(TangleSlider(min_value=0, max_value=20, step=0.1, suffix="% of the time", amount=0))
    return prob1, prob2


@app.cell
def _(alt, np, pd, prob1, prob2):
    cores = np.arange(1, 64 + 1)
    p1, p2 = prob1.amount/100, prob2.amount/100
    eff1 = 1/(p1 + (1-p1)/cores)
    eff2 = 1/(p2 + (1-p2)/cores)

    df_amdahl = pd.DataFrame({
        'cores': cores,
        f'{prob1.amount:.2f}% sync rate': eff1,
        f'{prob2.amount:.2f}% sync rate': eff2
    }).melt("cores")

    c = (
        alt.Chart(df_amdahl)
            .mark_line()
            .encode(
                x='cores',
                y=alt.Y('value').title("effective cores"),
                color="variable"
            )
            .properties(width=500, title="Comparison between cores and actual speedup.")
    )
    return (c,)


@app.cell(hide_code=True)
def _(c, mo, prob1, prob2):
    mo.vstack([
        mo.md(f"""
    You cannot always get a speedup by throwing more compute at a problem. Let's compare two scenarios.

    - You might have a parallel program that needs to sync up {prob1}.
    - Another parallel program needs to sync up {prob2}.
        """),
        c
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## TangleChoice
    """)
    return


@app.cell
def _(TangleChoice, TangleSlider, mo):
    saying = mo.ui.anywidget(TangleChoice(["🙂", "🎉", "💥"]))
    times = mo.ui.anywidget(TangleSlider(min_value=1, max_value=20, step=1, suffix=" times", amount=3))
    return saying, times


@app.cell
def _(mo, saying, times):
    mo.md(f"""
    As a quick demo, let's repeat {saying} {times}.

    {" ".join([saying.choice] * int(times.amount))}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## TangleSelect
    """)
    return


@app.cell
def _(TangleSelect, mo):
    shouting = mo.ui.anywidget(TangleSelect(["🥔", "🥕", "🍎"]))
    times2 = mo.ui.anywidget(TangleSlider(min_value=1, max_value=20, step=1, suffix=" times", amount=3))    
    return shouting, times2


@app.cell
def _(mo, shouting, times):
    mo.md(f"""
    As a quick demo, let's repeat {shouting} {times2}.

    {" ".join([shouting.choice] * int(times2.amount))}
    """)
    return


if __name__ == "__main__":
    app.run()
