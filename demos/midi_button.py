# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.29",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # MidiButton

    As a demo, you'll see a tiny state machine below. The **Play** and **Rec** are mutually-exclusive toggles, and the momentary **Stop** clears whichever is lit.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    from wigglystuff import MidiButton

    play = MidiButton(icon="play", label="Play", mode="toggle", color="#22c55e")
    stop = MidiButton(icon="stop", label="Stop", mode="momentary")
    record = MidiButton(icon="record", label="Rec", mode="toggle", color="#ef4444")


    # Observers keep the *buttons* in sync (this syncs to the browser). The
    # status markdown below is derived from press timestamps instead, because a
    # value set here from the kernel doesn't re-trigger marimo's reactive graph.
    def _exclusive_play(change):
        if play.value:
            record.value = False


    def _exclusive_record(change):
        if record.value:
            play.value = False


    def _stop_all(change):
        play.value = False
        record.value = False


    play.observe(_exclusive_play, names="value")
    record.observe(_exclusive_record, names="value")
    stop.observe(_stop_all, names="press_timestamp")

    play_ui = mo.ui.anywidget(play)
    stop_ui = mo.ui.anywidget(stop)
    record_ui = mo.ui.anywidget(record)
    mo.hstack([play_ui, stop_ui, record_ui], justify="center", gap=1)
    return MidiButton, play_ui, record_ui, stop_ui


@app.cell(hide_code=True)
def _(mo, play_ui, record_ui, stop_ui):
    # Most-recently-pressed pad wins, so this stays correct even after Stop
    # clears the toggles (a frontend press always bumps a timestamp).
    _pt = play_ui.value["press_timestamp"]
    _rt = record_ui.value["press_timestamp"]
    _st = stop_ui.value["press_timestamp"]
    if _st >= _pt and _st >= _rt:
        _state = "■ Stopped"
    elif _pt >= _rt:
        _state = "▶ Playing" if play_ui.value["value"] else "■ Stopped"
    else:
        _state = "● Recording" if record_ui.value["value"] else "■ Stopped"
    mo.md(f"**Transport:** {_state}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Emoji & text faces

    No built-in `icon` name? Pass any emoji, or skip the icon and the `label`
    renders on the pad face itself.
    """)
    return


@app.cell(hide_code=True)
def _(MidiButton, mo):
    boom = mo.ui.anywidget(MidiButton(icon="💥", size=72))
    mute = mo.ui.anywidget(MidiButton(label="Mute", mode="toggle", size=72))
    horn = mo.ui.anywidget(MidiButton(icon="🔊", size=72))
    mo.hstack([boom, mute, horn], justify="center", gap=1)
    return boom, horn, mute


@app.cell(hide_code=True)
def _(boom, horn, mo, mute):
    _last_ts, _last = max(
        (boom.value["press_timestamp"], "💥 Boom"),
        (horn.value["press_timestamp"], "🔊 Horn"),
    )
    mo.md(
        f"**Muted:** {'yes' if mute.value['value'] else 'no'} &nbsp;·&nbsp; "
        f"**Last sound:** {_last if _last_ts else '—'}"
    )
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
