import marimo

__generated_with = "0.18.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo

    from wigglystuff import GamepadWidget

    pad = mo.ui.anywidget(GamepadWidget())
    return mo, pad


@app.cell
def _(mo):
    mo.md(r"""
    ## Listen to browser gamepad events

    This widget streams button presses, d-pad status, and analog stick axes.
    Plug in a controller (or pair a Bluetooth one), press any button, and you should see data below.
    """)
    return


@app.cell
def _(pad):
    pad
    return


@app.cell
def _(mo, pad):
    axes = pad.axes if pad.axes else [0.0, 0.0, 0.0, 0.0]
    left_axes = tuple(round(val, 2) for val in axes[:2])
    right_axes = tuple(round(val, 2) for val in axes[2:])

    dpad_directions = [
        symbol
        for flag, symbol in [
            (pad.dpad_up, "↑"),
            (pad.dpad_down, "↓"),
            (pad.dpad_left, "←"),
            (pad.dpad_right, "→"),
        ]
        if flag
    ]

    last_button = pad.current_button_press if pad.current_button_press >= 0 else "—"
    current_ts = pad.current_timestamp or "—"
    previous_ts = pad.previous_timestamp or "—"

    mo.vstack(
        [
            mo.md(
                f"**Last button:** `{last_button}` &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"**Last change (ms):** `{current_ts}` &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"**Previous:** `{previous_ts}`"
            ),
            mo.md(
                f"**Sticks** &nbsp; Left: `{left_axes}` &nbsp; Right: `{right_axes}`"
            ),
            mo.md(
                "**D-pad:** "
                + (
                    " ".join(dpad_directions)
                    if dpad_directions
                    else "`—` (tap the arrows)"
                )
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
