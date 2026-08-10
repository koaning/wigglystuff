# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "numpy==2.4.3",
#     "wigglystuff==0.5.24",
# ]
# ///

import marimo

__generated_with = "0.23.16"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## EdgeDraw

    We created this widget to make it easy to dynamically draw a graph.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import EdgeDraw

    widget = mo.ui.anywidget(EdgeDraw(["a", "b", "c", "d"], directed=True))
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The widget has all sorts of useful attributes and properties that you can retreive. These update as you interact with the widget.
    """)
    return


@app.cell
def _(widget):
    widget.names
    return


@app.cell
def _(widget):
    widget.links
    return


@app.cell
def _(widget):
    widget.get_adjacency_matrix()
    return


@app.cell
def _(widget):
    widget.get_neighbors("c")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Cycle Detection

    The widget can detect cycles in the graph. You can specify whether to treat the graph as directed or undirected.
    """)
    return


@app.cell
def _(widget):
    widget.has_cycle(directed=False), widget.has_cycle(directed=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Editing nodes from Python

    You can add or remove nodes at runtime by updating `widget.names`.
    Traitlets only notices a change when you **reassign** the list, so build a
    new list (`widget.names = widget.names + ["e"]`) rather than mutating it in
    place with `.append()` — an in-place mutation never syncs to the drawing.
    """)
    return


@app.cell
def _(mo):
    name_input = mo.ui.text(placeholder="node name")
    add_button = mo.ui.run_button(label="Add node", kind="success")
    remove_button = mo.ui.run_button(label="Remove node", kind="danger")
    mo.hstack([name_input, add_button, remove_button], justify="start")
    return add_button, name_input, remove_button


@app.cell
def _(add_button, name_input, remove_button, widget):
    name = name_input.value.strip()
    if add_button.value and name and name not in widget.names:
        widget.names = widget.names + [name]
    if remove_button.value and name in widget.names:
        widget.names = [n for n in widget.names if n != name]
    return


if __name__ == "__main__":
    app.run()
