# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "wigglystuff",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    # Prefer the local checkout so this demo tracks the in-repo FloatingPanel
    # even before it lands in a published wigglystuff release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import CircularSlider, FloatingPanel

    return CircularSlider, FloatingPanel, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # FloatingPanel -- pin any marimo content above the notebook

    `FloatingPanel` wraps live marimo content in a `position: fixed` panel
    that stays in view while the notebook scrolls, is draggable by its
    header, and minimizes to just that header with the `−` toggle.

    It is a marimo-only display helper, not an `AnyWidget`. Display it as the
    last expression of a cell and keep reading `.value` off the widgets you
    passed in -- they stay fully live. Unlike `Pip`, the panel is an ordinary
    element in the page, so it works inside an iframe such as molab.
    """)
    return


@app.cell
def _(mo):
    slider = mo.ui.slider(0, 10, value=3, label="temperature")
    counter = mo.ui.button(value=0, label="click me", on_click=lambda v: v + 1)
    return counter, slider


@app.cell
def _(FloatingPanel, counter, mo, slider):
    # Float a small control panel in the top-right corner. Drag it by the header.
    # With no `width`, the panel shrink-wraps to its content.
    FloatingPanel(mo.vstack([slider, counter]), corner="top-right")
    return


@app.cell
def _(counter, mo, slider):
    # The floated widgets are untouched -- read them exactly as you normally would.
    mo.md(f"`slider.value` is **{slider.value}**, clicked **{counter.value}** times")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Any renderable works

    The `child` can be a single `mo.ui` element, a layout, a chart, an image,
    or another wigglystuff widget. Scroll -- the panels stay pinned.
    """)
    return


@app.cell
def _(CircularSlider, FloatingPanel):
    # A wigglystuff widget floated in the bottom-left corner (shrink-wrapped).
    dial = CircularSlider(value=40, label="volume")
    FloatingPanel(dial, corner="bottom-left")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Setting a width

    Leave `width` unset and the panel hugs its content. Pass an integer for
    a fixed width -- handy to reflow a longer note.
    """)
    return


@app.cell
def _(FloatingPanel, counter, mo, slider):
    note = mo.md(
        "**Tip:** drag me by the header, or minimize me with the −. "
        "A fixed `width` reflows this text to a tidy column."
        f"`slider.value` is **{slider.value}**, clicked **{counter.value}** times"
    )
    FloatingPanel(note, corner="bottom-right", width=240)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        "\n\n".join(
            f"### Section {i}\n" + ("Scroll down -- the panels stay put. " * 8) for i in range(12)
        )
    )
    return


if __name__ == "__main__":
    app.run()
