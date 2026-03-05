# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ProgressBar

    The `ProgressBar` widget gives you a progress bar that works across notebook runtimes without needing ipywidgets. You can update it from another cell in marimo, which the built-in progress bar does not allow.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import time
    from wigglystuff import ProgressBar

    return ProgressBar, mo, time


@app.cell
def _(ProgressBar, mo):
    progress = mo.ui.anywidget(ProgressBar(value=0, max_value=100))
    progress
    return (progress,)


@app.cell
def _(progress, time):
    progress.value = 0
    for _ in range(100):
        time.sleep(0.05)
        progress.value += 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Customization

    You can change the color, height, and hide the text label.
    """)
    return


@app.cell
def _(ProgressBar, mo):
    slim_bar = mo.ui.anywidget(
        ProgressBar(value=0, max_value=50, color="#3b82f6", height=12, show_text=False)
    )
    slim_bar
    return (slim_bar,)


@app.cell
def _(slim_bar, time):
    slim_bar.value = 0
    for _ in range(50):
        time.sleep(0.05)
        slim_bar.value += 1
    return


if __name__ == "__main__":
    app.run()
