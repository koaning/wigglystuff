import marimo

__generated_with = "0.17.8"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    from mohtml import div, tailwind_css

    tailwind_css()
    return (div,)


@app.cell
def _(div):
    div("hello there", klass="dark:bg-blue-500 bg-red-600")
    return


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

    widget = mo.ui.anywidget(EdgeDraw(["a", "b", "c", "d"]))
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
