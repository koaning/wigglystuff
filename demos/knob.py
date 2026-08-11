# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.24",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Knob
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import Knob

    gain = mo.ui.anywidget(
        Knob(min_value=0, max_value=11, value=5, ticks=12, label="Gain", color="tomato")
    )
    return Knob, gain


@app.cell
def _(Knob, mo):
    # A wider sweep with labelled endpoints, and a smaller pan-style knob.
    pan = mo.ui.anywidget(
        Knob(
            min_value=-1,
            max_value=1,
            step=0.05,
            value=0,
            ticks=[(-1, "L"), (0, "C"), (1, "R")],
            label="Pan",
        )
    )
    wide = mo.ui.anywidget(
        Knob(
            min_value=0,
            max_value=100,
            value=30,
            start_angle=-160,
            end_angle=160,
            ticks=5,
            size=110,
            label="Wide sweep",
        )
    )
    # A gapless full-circle knob (start_angle=0, end_angle=360) that wraps.
    full = mo.ui.anywidget(
        Knob(
            min_value=0,
            max_value=360,
            value=90,
            start_angle=0,
            end_angle=360,
            ticks=[(0, "N"), (90, "E"), (180, "S"), (270, "W")],
            label="Full circle",
        )
    )
    return full, pan, wide


@app.cell
def _(full, gain, mo, pan, wide):
    mo.hstack([gain, pan, wide, full], justify="center", gap=2)
    return


@app.cell(hide_code=True)
def _(full, gain, mo, pan, wide):
    mo.md(f"""
    **Gain:** `{gain.value['value']:.1f}` &nbsp;
    **Pan:** `{pan.value['value']:.2f}` &nbsp;
    **Wide:** `{wide.value['value']:.0f}` &nbsp;
    **Full:** `{full.value['value']:.0f}`
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
