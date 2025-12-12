# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "anywidget==0.9.21",
#     "numpy==2.3.5",
# ]
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def foobar():
    import marimo as mo
    from wigglystuff import CellTour
    return CellTour, mo


@app.cell
def _(CellTour, mo):
    # CellTour provides a simpler API than DriverTour
    # Just specify cell index, title, and description
    tour = mo.ui.anywidget(
        CellTour(steps=[
            {
                "cell": 0,
                "title": "Imports",
                "description": "First we import marimo and CellTour.",
            },
            {
                "cell": 1,
                "title": "Tour Definition",
                "description": "This cell defines the tour using the simplified API.",
            },
            {
                "cell": 2,
                "title": "Example Code",
                "description": "This cell shows some example code.",
            },
        ])
    )
    tour
    return


@app.cell
def _():
    # Example code cell
    x = 1
    y = 2
    z = x + y
    return


if __name__ == "__main__":
    app.run()
