# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.12",
# ]
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import GridDraw

    drawing = GridDraw(rows=10, cols=10, line_width=4, width=440, height=440, theme="light")
    drawing.add_dot(2, 2)
    drawing.add_line((3, 1), (3, 2), width=4)
    drawing.add_line((3, 2), (3, 3), width=4)
    grid = mo.ui.anywidget(drawing)
    return grid, mo


@app.cell
def _(grid):
    grid
    return


@app.cell(hide_code=True)
def _(grid, mo):
    mo.md(f"""
    **Dots**

    ```python
    {grid.value["dots"]}
    ```

    **Lines**

    ```python
    {grid.value["lines"]}
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
