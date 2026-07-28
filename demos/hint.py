# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "wigglystuff",
# ]
# ///

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    # Prefer the local checkout so this demo tracks the in-repo Hint even before
    # it lands in a published wigglystuff release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import CircularSlider, Hint, Matrix, WidgetDAG

    return Hint, WidgetDAG, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Hint -- annotate a widget in the notebook itself

    `Hint` wraps a live widget and curves an arrow from a short note to the
    widget's edge, so a reader knows what to interact with and why.

    It is a marimo-only display helper, not an `AnyWidget`. Display it as the
    last expression of a cell and keep reading `.value` off the widget you
    passed in -- `Hint` never gets in the way of your data.
    """)
    return


@app.cell
def _(mo):
    n = mo.ui.slider(1, 10, value=4, label="N")
    return (n,)


@app.cell
def _(Hint, mo, n):
    # Either form works: a plain str is passed through mo.md for you, and an
    # mo.md object is rendered as-is. Both give you **bold**, `code` and links.
    Hint(n, mo.md("drag to change **N**"))
    return


@app.cell
def _(mo, n):
    # The wrapped widget is untouched -- read it exactly as you normally would.
    mo.md(f"`n.value` is **{n.value}**")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Placement

    `side=` puts the note on any of the four sides. Left/right lay the note
    beside the widget, top/bottom above or below it.
    """)
    return


@app.cell(hide_code=True)
def _(Hint, mo):
    # A Hint renders as ordinary marimo content, so it drops straight into an
    # mo.hstack alongside other hints.
    mo.hstack(
        [
            Hint(mo.ui.slider(1, 10, value=3), "side='right'"),
            Hint(mo.ui.slider(1, 10, value=3), "side='left'", side="left"),
        ],
        gap=4,
        justify="start",
    )
    return


@app.cell(hide_code=True)
def _(Hint, mo):
    mo.hstack(
        [
            Hint(mo.ui.slider(1, 10, value=3), "side='top'", side="top"),
            Hint(mo.ui.slider(1, 10, value=3), "side='bottom'", side="bottom"),
        ],
        gap=4,
        justify="start",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## With other layouts

    The hint mechanism is amazing when it isn't clear that you can interact with something.
    """)
    return


@app.cell
def _(Hint, WidgetDAG, mo, temp, tokens):
    wd = WidgetDAG(
        {
            "temp": temp,
            "tokens": tokens,
            "cost": mo.md(f"~${temp.value * tokens.value / 5000:.2f}"),
        },
        [("temp", "cost"), ("tokens", "cost")],
    )

    Hint(wd, "you can change these sliders!", side="top")
    return


@app.cell
def _(mo):
    temp = mo.ui.slider(0, 2, value=0.7, step=0.1, label="temperature")
    return (temp,)


@app.cell
def _(mo):
    tokens = mo.ui.slider(100, 4000, value=1200, step=100, label="max tokens")
    return (tokens,)


if __name__ == "__main__":
    app.run()
