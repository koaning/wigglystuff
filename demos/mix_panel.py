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
    # MixPanel

    A rack of nested `Knob`/`Fader` widgets. The children are mounted *inside*
    the panel via anywidget's widget-composition host (needs `anywidget>=0.11`).
    Each child still syncs its own `value`, and the panel aggregates them into a
    combined `values` dict.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import MixPanel, Knob, Fader, Slider2D

    panel = mo.ui.anywidget(
        MixPanel(
            {
                "gain": Knob(min_value=0, max_value=11, value=5, ticks=6, label="Gain"),
                # A stepped rotary selector (discrete detents).
                "mode": Knob(
                    steps=[(0, "Off"), (1, "Low"), (2, "Mid"), (3, "Hi")],
                    value=1, label="Mode",
                ),
                "level": Fader(
                    min_value=-60, max_value=6, value=0,
                    ticks=[(-60, "-60"), (-20, "-20"), (0, "0"), (6, "+6")],
                    label="Level",
                ),
                # A nested 2D slider — MixPanel aggregates its (x, y).
                "xy": Slider2D(x=0.3, y=-0.2, width=90, height=90),
            },
            title="Channel 1",
        )
    )
    panel
    return (panel,)


@app.cell(hide_code=True)
def _(mo, panel):
    mo.md(f"""
    **Combined values:** `{panel.value['values']}`
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
