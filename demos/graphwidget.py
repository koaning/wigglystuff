# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.5.2",
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

    from wigglystuff import GraphWidget, PlaySlider

    return GraphWidget, PlaySlider, mo


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
            height=420,
            directed=False
        )
    )
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell(hide_code=True)
def _(add_node, mo):
    mo.ui.button(label="Add node from Python", on_click=add_node)
    return


@app.cell(hide_code=True)
def _(mo, widget):
    mo.vstack(
        [
            mo.md(f"**Hovered node:** `{widget.hovered_node}`"),
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
def _(widget):
    def add_node(_):
        index = len(widget.nodes) + 1
        new_id = widget.add_node(
            f"Node {index}",
            color="#b45309" if index % 2 else "#2563eb",
            size=12 + index,
        )
        widget.add_edge("Alpha", new_id, name="added")

    return (add_node,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Random growth graph

    Generate a random graph from scratch. At each step, a new node is added and connected randomly to an existing node in the graph.
    """)
    return


@app.cell
def _(mo):
    num_nodes = mo.ui.slider(start=10, stop=100, step=5, value=40, label="Number of nodes")
    regenerate_button = mo.ui.button(label="Regenerate Graph")
    mo.hstack([num_nodes, regenerate_button])
    return num_nodes, regenerate_button


@app.cell(hide_code=True)
def _(num_nodes, regenerate_button):
    import random

    # Trigger generation on button click or slider changes
    _trigger = regenerate_button.value

    # Generate the growth steps
    steps = []

    # Step 0: start with 1 node
    _nodes = [{"id": "0", "name": "Node 0"}]
    _edges = []
    steps.append({
        "nodes": list(_nodes),
        "edges": list(_edges),
        "new_node": "0",
        "connected_to": None
    })

    for i in range(1, num_nodes.value):
        _new_node_id = str(i)
        # Select a random existing node to connect to
        _existing_node = random.choice(_nodes)
        _existing_id = _existing_node["id"]

        # Add new node
        _new_node = {
            "id": _new_node_id,
            "name": f"Node {i}"
        }
        _nodes.append(_new_node)

        # Add new edge
        _new_edge = {
            "source": _existing_id,
            "target": _new_node_id
        }
        _edges.append(_new_edge)

        steps.append({
            "nodes": list(_nodes),
            "edges": list(_edges),
            "new_node": _new_node_id,
            "connected_to": _existing_id
        })

    max_step = len(steps) - 1
    return max_step, steps


@app.cell(hide_code=True)
def _(PlaySlider, max_step, mo):
    play = mo.ui.anywidget(
        PlaySlider(
            min_value=0,
            max_value=max_step,
            step=1,
            interval_ms=300,
            loop=False,
        )
    )
    play
    return (play,)


@app.cell(hide_code=True)
def _(max_step, play, steps):
    step_index = int(play.value.get("value", 0))
    step_index = max(0, min(step_index, max_step))
    step = steps[step_index]
    return step, step_index


@app.cell(hide_code=True)
def _(GraphWidget, mo):
    growth_graph = mo.ui.anywidget(
        GraphWidget(
            nodes=[],
            edges=[],
            directed=False,
            bounded=False,
            width=720,
            height=460,
        )
    )
    growth_graph
    return (growth_graph,)


@app.cell
def _(growth_graph, step):
    _new_node_id = step["new_node"]
    _connected_to_id = step["connected_to"]

    _nodes = []
    for _node in step["nodes"]:
        _node_copy = dict(_node)
        if _node_copy["id"] == _new_node_id:
            _node_copy["color"] = "#10b981"  # Emerald/green for the newly added node
            _node_copy["size"] = 16
        elif _node_copy["id"] == _connected_to_id:
            _node_copy["color"] = "#ef4444"  # Red for the node it connected to
            _node_copy["size"] = 14
        else:
            _node_copy["color"] = "#3b82f6"  # Blue for normal nodes
            _node_copy["size"] = 11
        _nodes.append(_node_copy)

    _edges = []
    for _edge in step["edges"]:
        _edge_copy = dict(_edge)
        if (_edge_copy["source"] == _connected_to_id and _edge_copy["target"] == _new_node_id) or \
           (_edge_copy["source"] == _new_node_id and _edge_copy["target"] == _connected_to_id):
            _edge_copy["color"] = "#f59e0b"  # Amber for the new edge
            _edge_copy["width"] = 3
        else:
            _edge_copy["color"] = "#cbd5e1"  # Slate-300 for existing edges
            _edge_copy["width"] = 1.5
        _edges.append(_edge_copy)

    with growth_graph.hold_sync():
        growth_graph.nodes = _nodes
        growth_graph.edges = _edges
    return


@app.cell
def _(growth_graph, max_step, mo, step_index):
    mo.vstack(
        [
            mo.md(f"**Step:** `{step_index}` / `{max_step}`"),
            mo.md(f"**Hovered node:** `{growth_graph.hovered_node}`"),
            mo.md(f"**Selected nodes:** `{growth_graph.selected_nodes}`"),
            mo.md(f"**Selected edges:** `{growth_graph.selected_edges}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
