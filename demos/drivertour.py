# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "anywidget==0.9.21",
#     "marimo",
#     "numpy==2.3.5",
# ]
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="columns", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    from wigglystuff import DriverTour
    return (DriverTour,)


@app.cell
def _(tour):
    tour.steps
    return


@app.cell(hide_code=True)
def _(DriverTour, mo):
    tour = mo.ui.anywidget(
        DriverTour(steps=[
            {
                "element": ".marimo-cell",
                "index": 0,
                "popover": {
                    "title": "Welcome!",
                    "description": "In this first cell we do a bunch of imports.",
                    "position": "center"
                }
            },
            { 
                "element": ".marimo-cell",
                "index": 1,
                "popover": {
                    "title": "Fancy!",
                    "description": "But in this cell we define a tour! Fancy that!",
                    "position": "center"
                }
            }, 
            { 
                "element": ".marimo-cell",
                "index": 2,
                "popover": {
                    "title": "Steps",
                    "description": "You can also inspect the steps at the end here.",
                    "position": "center"
                }
            }, 

        ])
    )
    tour
    return (tour,)


if __name__ == "__main__":
    app.run()
