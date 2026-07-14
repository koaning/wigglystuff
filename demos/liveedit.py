# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "anywidget",
#     "dicekit",
#     "drawdata",
#     "marimo",
#     "numpy",
#     "wigglystuff==0.5.14",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import LiveEdit

    return LiveEdit, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## LiveEdit

    `LiveEdit.inspect_run(...)` records one run of a Python function and shows
    how loop variables change pass by pass. Hover a variable or loop in either
    panel to connect the code with the trace. Click a numeric column header to
    plot it across passes — plain click for a fresh chart, ⌘/Ctrl-click to
    overlay on the same axes, Shift-click to stack a new chart below (shared
    iteration axis). Pass `float_precision=` to trim wide float columns and
    `visible_columns=` to show only the variables you care about.
    """)
    return


@app.function
def binary_search(key, array):
    low = 0
    high = len(array) - 1

    while low <= high:
        mid = (low + high) // 2
        value = array[mid]
        if value < key:
            low = mid + 1
        elif value > key:
            high = mid - 1
        else:
            return mid

    return -1


@app.cell
def _(LiveEdit, mo):
    binary_trace = mo.ui.anywidget(
        LiveEdit.inspect_run(binary_search, key="q", array=list("abcdefghijklmnopqrstuvwxyz"))
    )
    binary_trace
    return


@app.cell
def _(LiveEdit):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a


    LiveEdit.inspect_run(gcd, 2**5, 2**4 + 1)
    return


@app.cell
def _(LiveEdit):
    def insertion_sort(values):
        values = values[:]
        for i in range(1, len(values)):
            key = values[i]
            j = i - 1
            while j >= 0 and values[j] > key:
                values[j + 1] = values[j]
                j = j - 1
            values[j + 1] = key
        return values


    LiveEdit.inspect_run(insertion_sort, [5, 2, 4, 3, 1])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    When a run raises, the trace stops at the failing pass. The failing source
    line is highlighted with an inline message, the loop pass where execution
    stopped is marked with a `✗`, and the widget reports `raised <ErrorType>`.
    """)
    return


@app.cell
def _(LiveEdit):
    def insertion_sort_boom(values):
        values = values[:]
        for i in range(1, len(values)):
            key = values[i]
            j = i - 1
            while j >= 0 and values[j] > key:
                values[j + 1] = values[j]
                j = j - 1
            values[j + 1] = key
        return values


    # The trailing "a" makes `1 > "a"` raise a TypeError mid-run.
    LiveEdit.inspect_run(insertion_sort_boom, [5, 2, 4, 3, 1, "a"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Rich HTML values

    When a traced value exposes a rich representation (`_repr_html_`, marimo's
    `_mime_`/`_display_`), the trace panel renders that HTML inline instead of
    the plain `repr`. Any value assigned to a variable or returned shows up —
    no `print` needed.
    """)
    return


@app.cell
def _(LiveEdit):
    class Bar:
        """A value whose HTML repr is a little colored bar."""

        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return f"Bar({self.value})"

        def _repr_html_(self):
            width = min(self.value, 100)
            return (
                '<div style="display:flex;align-items:center;gap:6px">'
                f'<div style="background:#0969da;height:14px;'
                f'border-radius:3px;width:{width}px"></div>'
                f"<span>{self.value}</span>"
                "</div>"
            )


    def running_totals(steps):
        total = 0
        bar = Bar(0)
        for step in steps:
            total = total + step
            bar = Bar(total)
        return bar


    LiveEdit.inspect_run(running_totals, [10, 15, 30, 25])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Real-world showcase: `dicekit`

    A [`dicekit`](https://github.com/koaning/dicekit) `Dice` has a boring
    `repr` (just an object address) but a rich `_repr_html_` that draws its
    probability distribution. As we add dice together, the trace shows the
    running distribution chart for every pass — no `print`, just plain
    assignments.
    """)
    return


@app.cell
def _(LiveEdit):
    from dicekit import Dice


    def sum_of_dice(n):
        total = Dice.from_sides(6)
        for _ in range(n - 1):
            total = total + total
        return total


    LiveEdit.inspect_run(sum_of_dice, 8)
    return


@app.cell
def _(LiveEdit):
    import numpy as np


    def gradient_descent(start, steps=12):
        x = start
        lr = 0.4
        for step in range(steps):
            grad = 2 * (x - 3)
            x = x - lr * grad
            loss = (x - 3) ** 2
            lr = np.sin(step * np.pi / steps) * lr + 0.1
        return x


    # `float_precision` keeps the table readable; charts still use full values.
    # Click `loss` to watch it decay, then Shift-click `lr` to stack a second
    # chart below it (same iteration axis, its own y-axis).
    LiveEdit.inspect_run(gradient_descent, 12.0, steps=12, float_precision=4)
    return


if __name__ == "__main__":
    app.run()
