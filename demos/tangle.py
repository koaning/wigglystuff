# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.19.4",
#     "numpy==2.4.1",
#     "pandas==2.3.3",
#     "wigglystuff==0.5.26",
# ]
# ///

import marimo

__generated_with = "0.23.16"
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
    coffees = mo.ui.anywidget(TangleSlider(amount=10, min_value=0, max_value=10_000, step=1, suffix=" coffees", digits=0))
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

    def speedup(percent):
        p = percent / 100
        return 1 / (p + (1 - p) / cores)

    label1 = f'{prob1.amount:.2f}% sync rate'
    label2 = f'{prob2.amount:.2f}% sync rate'
    df_amdahl = pd.DataFrame({
        'cores': cores,
        label1: speedup(prob1.amount),
        label2: speedup(prob2.amount),
    }).melt("cores")

    # committed_amount holds the value from before the drag, so while you drag
    # these dashed lines show where the curves were.
    df_before = pd.DataFrame({
        'cores': cores,
        'before 1': speedup(prob1.committed_amount),
        'before 2': speedup(prob2.committed_amount),
    }).melt("cores")

    # Each slider keeps its own color, for its live line and its dashed one.
    colors = ["#4c78a8", "#f58518"]
    before = (
        alt.Chart(df_before)
            .mark_line(strokeDash=[4, 4])
            .encode(
                x='cores',
                y='value',
                color=alt.Color('variable', scale=alt.Scale(domain=['before 1', 'before 2'], range=colors), legend=None),
            )
    )
    lines = (
        alt.Chart(df_amdahl)
            .mark_line()
            .encode(
                x='cores',
                y=alt.Y('value').title("effective cores"),
                color=alt.Color('variable', scale=alt.Scale(domain=[label1, label2], range=colors)),
            )
    )
    c = (
        (before + lines)
            .resolve_scale(color='independent')
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

    While you drag, `amount` follows along and `committed_amount` keeps the value from before the drag, drawn as the dashed line.
        """),
        c
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Fine control & exact values

    While dragging you can hold a modifier key to change the scrub speed:

    - Hold **Shift** for 10&times; *coarser* steps &mdash; cover a big range fast.
    - Hold **Alt / Option** for 10&times; *finer* steps &mdash; dial in a precise value.

    Toggle the modifier mid-drag and the value rescales smoothly instead of
    jumping. You can also **click** a slider to type an exact value, including
    scientific notation like `2.5e-3`. Typed values are clamped to the bounds but
    keep their exact value (they are *not* snapped to `step`).
    """)
    return


@app.cell
def _(TangleSlider, mo):
    unit_cost = mo.ui.anywidget(
        TangleSlider(amount=0.002, min_value=0, max_value=1, step=0.0001, prefix="$", digits=4)
    )
    return (unit_cost,)


@app.cell(hide_code=True)
def _(mo, unit_cost):
    mo.md(f"""
    Say each API call costs {unit_cost}.

    - Hold **Alt/Option** and drag to nudge it by fractions of a cent.
    - Click it and type `2.5e-3` to set an exact price &mdash; the `$` prefix
      stays put and the value reads back as you typed it.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## TangleSlider with steps

    You can pass explicit `steps` for non-linear ranges, just like `mo.ui.slider`.
    """)
    return


@app.cell
def _(TangleSlider, mo, np):
    learning_rate = mo.ui.anywidget(
        TangleSlider(steps=np.logspace(-4, 3, 8), digits=4, suffix="x")
    )
    return (learning_rate,)


@app.cell(hide_code=True)
def _(learning_rate, mo):
    mo.md(f"""
    The current multiplier is {learning_rate}. Drag to cycle through orders of magnitude.
    """)
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
def _(TangleSelect, TangleSlider, mo):
    shouting = mo.ui.anywidget(TangleSelect(["🥔", "🥕", "🍎"]))
    times2 = mo.ui.anywidget(TangleSlider(min_value=1, max_value=20, step=1, suffix=" times", amount=3))    
    return shouting, times2


@app.cell
def _(mo, shouting, times2):
    mo.md(f"""
    As a quick demo, let's repeat {shouting} {times2}.

    {" ".join([shouting.choice] * int(times2.amount))}
    """)
    return


if __name__ == "__main__":
    app.run()
