# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo", "wigglystuff", "rich"
# ]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ProgressBar

    The `ProgressBar` widget gives you a progress bar that works across notebook runtimes without needing ipywidgets. You can update it from another cell in marimo, which the built-in progress bar does not allow.

    The same widget also has a trick up its sleeve: run this notebook as a script
    (with [`rich`](https://github.com/Textualize/rich) installed) and the bars
    render as fancy animated progress bars **in the terminal** instead. marimo
    knows which mode it is in via `mo.app_meta().mode` (`"edit"`/`"run"` in the
    browser, `"script"` on the command line), and `ProgressBar` uses the same
    signal to pick its renderer automatically. No code changes needed either way.
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
    progress.widget.value = 0
    for _ in range(100):
        time.sleep(0.05)
        progress.widget.value += 1
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
    slim_bar.widget.value = 0
    for _ in range(50):
        time.sleep(0.05)
        slim_bar.widget.value += 1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Moving backward

    `value` is absolute, so the bar can also *retreat* — handy when a step fails
    and you have to retry. In the browser the fill shrinks; run as a script and
    the rich bar shrinks the same way.
    """)
    return


@app.cell
def _(ProgressBar, mo):
    retry_bar = mo.ui.anywidget(ProgressBar(value=0, max_value=30, color="#f59e0b"))
    retry_bar
    return (retry_bar,)


@app.cell
def _(retry_bar, time):
    # climb to 20, stumble back to 10, then finish
    forward = list(range(0, 21))
    back = list(range(19, 9, -1))
    finish = list(range(11, 31))
    retry_bar.widget.value = 0
    for _v in forward + back + finish:
        time.sleep(0.06)
        retry_bar.widget.value = _v
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Script mode

    Nothing above changes for the terminal — the loops in this notebook drive
    `.value`, and when the notebook runs as a script those exact assignments
    animate a rich bar in the terminal (spinner, colored bar, percentage, count
    and a time-remaining estimate). `rich` must be installed for this
    (`pip install rich`); then run:

    ```
    uv run --with rich python demos/progressbar.py
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
