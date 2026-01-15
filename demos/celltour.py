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
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def foobar():
    # Notice how this cell has a name?
    import marimo as mo
    from wigglystuff import CellTour
    return CellTour, mo


@app.cell
def _(CellTour, mo):
    # CellTour provides a simpler API than DriverTour
    # You can use cell indices OR cell names (data-cell-name attribute)
    tour = mo.ui.anywidget(
        CellTour(
            steps=[
                {
                    # Use cell_name to target cells by their function name
                    "cell_name": "foobar",
                    "title": "Imports",
                    "description": "First we import marimo and CellTour.",
                },
                {
                    "cell": 1,
                    "title": "Tour Definition",
                    "description": "This cell defines the tour using the simplified API.",
                },
                {
                    # Use cell_name for the example cell
                    "cell": 2,
                    "title": "Example Code",
                    "description": "This cell shows some example code.",
                },
            ]
        )
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
