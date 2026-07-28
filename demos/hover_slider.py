# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.22",
# ]
# ///

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # HoverSlider

    Sweep the pointer across the track: the dashed marker and `hover_value`
    follow the pointer while the puck and `value` stay where you last clicked.
    Click or drag to commit. Arrow keys work too.
    """)
    return


@app.cell
def _():
    import marimo as mo
    from wigglystuff import HoverSlider

    linear = mo.ui.anywidget(
        HoverSlider(start=0, stop=100, step=1, value=42, label="linear")
    )
    linear
    return HoverSlider, linear, mo


@app.cell(hide_code=True)
def _(linear, mo):
    mo.md(f"""
    | | |
    | --- | --- |
    | committed `value` | `{linear.value["value"]}` |
    | live `hover_value` | `{linear.value["hover_value"]}` |
    | `hovering` | `{linear.value["hovering"]}` |
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Discrete `steps`

    `steps` snaps to a list of values and lays them out *evenly* across the
    track, so wildly spaced values stay reachable. Types survive the round
    trip: these are `int`s, not `float`s.
    """)
    return


@app.cell
def _(HoverSlider, mo):
    powers = mo.ui.anywidget(
        HoverSlider(steps=[1, 10, 100, 1000, 10000], label="batch size")
    )
    powers
    return (powers,)


@app.cell(hide_code=True)
def _(mo, powers):
    hovered = powers.value["hover_value"]
    committed = powers.value["value"]
    mo.md(
        f"""
        Previewing **{hovered}** rows (`{type(hovered).__name__}`),
        committed to **{committed}**.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Previewing an expensive result

    The point of two values: show a cheap preview of what `hover_value` would
    give you, and only commit the real thing on click.
    """)
    return


@app.cell
def _(HoverSlider, mo):
    threshold = mo.ui.anywidget(
        HoverSlider(
            start=0.0,
            stop=1.0,
            step=0.05,
            value=0.5,
            label="threshold",
            color="tomato",
            sync_throttle_ms=1000,
        )
    )
    threshold
    return (threshold,)


@app.cell(hide_code=True)
def _(mo, threshold):
    scores = [0.04, 0.12, 0.28, 0.31, 0.47, 0.55, 0.61, 0.78, 0.83, 0.91]
    preview = threshold.value["hover_value"]
    kept = [s for s in scores if s >= preview]
    mo.md(
        f"""
        At a threshold of **{preview:.2f}** you'd keep **{len(kept)} / {len(scores)}**
        scores: `{kept}`

        Committed threshold: **{threshold.value["value"]:.2f}**
        """
    )
    return


if __name__ == "__main__":
    app.run()
