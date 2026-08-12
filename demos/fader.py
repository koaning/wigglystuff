# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.25",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Fader
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import Fader

    level = mo.ui.anywidget(
        Fader(
            min_value=-60,
            max_value=6,
            value=0,
            ticks=[(-60, "-60"), (-20, "-20"), (-6, "-6"), (0, "0"), (6, "+6")],
            label="Level (dB)",
        )
    )
    return Fader, level


@app.cell
def _(Fader, mo):
    send = mo.ui.anywidget(
        Fader(min_value=0, max_value=100, value=75, ticks=5, label="Send", color="teal")
    )
    crossfade = mo.ui.anywidget(
        Fader(
            min_value=0,
            max_value=1,
            step=0.01,
            value=0.5,
            orientation="horizontal",
            ticks=[(0, "A"), (1, "B")],
            length=180,
            label="Crossfade",
        )
    )
    return crossfade, send


@app.cell
def _(crossfade, level, mo, send):
    mo.hstack([level, send, crossfade], justify="center", align="center", gap=2)
    return


@app.cell(hide_code=True)
def _(crossfade, level, mo, send):
    mo.md(f"""
    **Level:** `{level.value['value']:.1f} dB` &nbsp;
    **Send:** `{send.value['value']:.0f}` &nbsp;
    **Crossfade:** `{crossfade.value['value']:.2f}`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## MIDI learn

    Click the **MIDI** button, then move a control on your hardware — the next
    control-change message binds to the fader (like Ableton). The binding is
    remembered in your browser (keyed by the fader's `label`), so it survives a
    kernel restart or cell re-run. Needs a Chromium browser and a connected MIDI
    device; right-click the button to clear.
    """)
    return


@app.cell
def _(Fader, mo):
    midi_fader = mo.ui.anywidget(
        Fader(min_value=0, max_value=127, value=64, midi=True, label="MIDI")
    )
    midi_fader
    return (midi_fader,)


@app.cell(hide_code=True)
def _(midi_fader, mo):
    mo.md(f"""
    **Value:** `{midi_fader.value['value']:.0f}` &nbsp;
    **Bound CC:** `{midi_fader.value['midi_cc']}` &nbsp;
    **Device:** `{midi_fader.value['midi_device'] or '—'}`
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
