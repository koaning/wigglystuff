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
app = marimo.App(width="medium", sql_output="polars")


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This notebook is inspired by the [Fiddler on the Proof](https://thefiddler.substack.com/p/can-you-win-the-world-cup) mailing list. Check it out if you haven't already!

    ## The Riddle

    Here's the riddle we want to tackle.

    > Congratulations to Fiddler Nation for making it to the semifinals of the World Cup! All four teams that made it this far are equally matched in that they each possess the same total amount of “energy.” In advance of each semifinal game, teams must independently decide how much of their energy to allocate to the match; all remaining energy goes toward the finals. The team that spends more energy in any given game will win. The semifinals and finals occur so close in time that teams can’t recuperate any of their energy in between.

    > You’ve heard that the managers for the other three teams are abysmal and have no idea how to allocate their teams’ energy. Each of the other managers will independently pick a random percentage between 0 and 100 and allocate that portion of their team’s energy to the semifinal game; the rest of that team’s energy will go toward the final.

    > Since you’re the cleverest manager of the bunch, you can choose an optimal strategy that will maximize Fiddler Nation’s probability of winning the World Cup. What is this optimal probability?

    So let's model this. I will assume that we represent player 3.
    """)
    return


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
    grp1_energy_left = 100 - ordered(e1, e2)[0]
    return (grp1_energy_left,)


@app.cell
def _(e3):
    grp2_energy_left = 100 - e3
    return (grp2_energy_left,)


@app.cell
def _(e3, e4, p):
    p_win_first = p(e3 > e4)
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
        [e1, e2, slider, grp1_energy_left, grp2_energy_left, p_win_first, p_win, p_win_second]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    from wigglystuff import ScatterLog

    # Created once, in a cell with no dependencies, so it survives re-runs and
    # can accumulate a history as you sweep the slider.
    log = mo.ui.anywidget(
        ScatterLog(x_label="my energy", y_label="p(win)", max_points=500)
    )
    return (log,)


@app.cell
def _(log):
    log
    return


@app.cell
def _(log, p_win, p_win_first, p_win_second, slider):
    # # Depends on slider + the probabilities, so it re-runs every time you move
    # # the slider. Pass every series you want to track as a keyword -- each name
    # # becomes its own legend entry. Sweep the slider to trace them vs energy.
    log.append(
        x=slider.value,
        p_win=float(p_win),
        p_win_first=float(p_win_first),
        p_win_second=float(p_win_second),
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
