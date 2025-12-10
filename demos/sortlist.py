import marimo

__generated_with = "0.18.1"
app = marimo.App(width="columns", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import SortableList
    return SortableList, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `SortableList`

    This widget lets you maintain a list that you can sort around.
    """)
    return


@app.cell
def _(SortableList, mo):
    widget = mo.ui.anywidget(
        SortableList(
            ["a", "b", "c"],
            editable=True,
            addable=True,
            removable=True,
            label="My Sortable List"
        )

    )
    widget
    return (widget,)


@app.cell
def _(widget):
    widget.value.get("value")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
