# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.5.0",
# ]
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import GraphWidget

    return GraphWidget, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Programmatic graph

    Nodes and edges are defined from Python. Click nodes or edges in the widget to sync selections back to Python.
    """)
    return


@app.cell
def _(GraphWidget, mo):
    widget = mo.ui.anywidget(
        GraphWidget(
            nodes=[
                "Alpha",
                7,
                {"name": "Beta", "size": 20, "color": "#0f766e"},
                {"id": "gamma", "name": "Gamma", "color": "#7c3aed", "size": 17},
                {"name": "Delta", "data": {"kind": "generated"}},
            ],
            edges=[
                ("Alpha", "Beta"),
                {"source": "Beta", "target": "gamma", "name": "depends on", "width": 3},
                {"source": "gamma", "target": "7", "name": "scores"},
                ("Delta", "Alpha"),
            ],
            width=720,
            height=420,
        )
    )
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    mo.vstack(
        [
            mo.md(f"**Selected nodes:** `{widget.selected_nodes}`"),
            mo.md(f"**Selected edges:** `{widget.selected_edges}`"),
        ]
    )
    return


@app.cell
def _(widget):
    widget.get_selected_node_data()
    return


@app.cell
def _(widget):
    widget.get_selected_edge_data()
    return


@app.cell
def _(mo, widget):
    def add_node(_):
        index = len(widget.nodes) + 1
        new_id = widget.add_node(
            f"Node {index}",
            color="#b45309" if index % 2 else "#2563eb",
            size=12 + index,
        )
        widget.add_edge("Alpha", new_id, name="added")

    mo.ui.button(label="Add node from Python", on_click=add_node)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Directed graph

    Directed graphs use arrowheads to show flow direction.
    """)
    return


@app.cell
def _(GraphWidget, mo):
    directed = mo.ui.anywidget(
        GraphWidget(
            nodes=[
                {"name": "request", "color": "#2563eb", "size": 18},
                {"name": "validate", "color": "#0f766e"},
                {"name": "score", "color": "#7c3aed"},
                {"name": "approve", "color": "#15803d"},
                {"name": "review", "color": "#b45309"},
            ],
            edges=[
                {"source": "request", "target": "validate", "name": "submit"},
                {"source": "validate", "target": "score", "name": "valid"},
                {"source": "score", "target": "approve", "name": "high"},
                {"source": "score", "target": "review", "name": "low"},
                {"source": "review", "target": "validate", "name": "fix"},
            ],
            width=720,
            height=360,
            directed=True
        )
    )
    directed
    return (directed,)


@app.cell
def _(directed, mo):
    mo.vstack(
        [
            mo.md(f"**Directed nodes:** `{directed.selected_nodes}`"),
            mo.md(f"**Directed edges:** `{directed.selected_edges}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
