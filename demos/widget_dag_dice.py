# /// script
# dependencies = [
#     "dicekit",
#     "hastyplot==0.4.1",
#     "marimo",
#     "pandas==3.0.3",
#     "wigglystuff==0.5.20",
# ]
# requires-python = ">=3.12"
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="columns", sql_output="polars")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    # Prefer the local checkout so this notebook uses the in-repo (fixed)
    # WidgetDAG rather than the pinned published wigglystuff.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from dicekit import Dice, ordered, p
    from wigglystuff import WidgetDAG

    return Dice, WidgetDAG, mo, ordered, p


@app.cell
def _(Dice):
    e1 = Dice.from_numbers(*range(1, 101))
    e2 = Dice.from_numbers(*range(1, 101))
    return e1, e2


@app.cell
def _(mo):
    slider = mo.ui.slider(1, 101, label="my energy")
    return (slider,)


@app.cell
def _(Dice, slider):
    e3 = Dice.from_numbers(*[slider.value])
    return (e3,)


@app.cell
def _(Dice):
    e4 = Dice.from_numbers(*range(1, 101))
    return (e4,)


@app.cell
def _(e1, e2, ordered):
    grp1_energy_left = 100 - ordered(e1, e2)[-1]
    return (grp1_energy_left,)


@app.cell
def _(e3, e4, ordered):
    grp2_energy_left = 100 - ordered(e3, e4)[-1]
    return (grp2_energy_left,)


@app.cell
def _(e4, p, slider):
    p_win_first = p(slider.value > e4)
    return (p_win_first,)


@app.cell
def _(grp1_energy_left, grp2_energy_left, p):
    p_win_second = p(grp2_energy_left > grp1_energy_left)
    return (p_win_second,)


@app.cell
def _(p_win_first, p_win_second):
    p_win = p_win_first * p_win_second
    return (p_win,)


@app.cell
def _(
    WidgetDAG,
    e1,
    e2,
    grp1_energy_left,
    grp2_energy_left,
    p_win,
    p_win_first,
    p_win_second,
    slider,
):
    WidgetDAG.from_widgets(
        [e1, e2, slider, grp1_energy_left, grp2_energy_left, p_win_first, p_win_second, p_win]
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
