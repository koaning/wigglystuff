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
            width=720,
            height=420,
            directed=False
        )
    )
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(add_node, mo):
    mo.ui.button(label="Add node from Python", on_click=add_node)
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


@app.cell
def _(num_nodes, regenerate_button):
    import random

    # Trigger generation on button click or slider changes
    _trigger = regenerate_button.value

    # Generate the growth steps
    steps = []

    # Step 0: start with 1 node
    nodes = [{"id": "0", "name": "Node 0"}]
    edges = []
    steps.append({
        "nodes": list(nodes),
        "edges": list(edges),
        "new_node": "0",
        "connected_to": None
    })

    for i in range(1, num_nodes.value):
        new_node_id = str(i)
        # Select a random existing node to connect to
        existing_node = random.choice(nodes)
        existing_id = existing_node["id"]

        # Add new node
        new_node = {
            "id": new_node_id,
            "name": f"Node {i}"
        }
        nodes.append(new_node)

        # Add new edge
        new_edge = {
            "source": existing_id,
            "target": new_node_id
        }
        edges.append(new_edge)

        steps.append({
            "nodes": list(nodes),
            "edges": list(edges),
            "new_node": new_node_id,
            "connected_to": existing_id
        })

    max_step = len(steps) - 1
    return max_step, steps


@app.cell
def _(PlaySlider, max_step, mo):
    play = mo.ui.anywidget(
        PlaySlider(
            min_value=0,
            max_value=max_step,
            step=1,
            interval_ms=300,
            loop=False,
            width=720,
        )
    )
    play
    return (play,)


@app.cell
def _(max_step, play, steps):
    step_index = int(play.value.get("value", 0))
    step_index = max(0, min(step_index, max_step))
    step = steps[step_index]
    return step, step_index


@app.cell
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
    new_node_id = step["new_node"]
    connected_to_id = step["connected_to"]

    nodes = []
    for node in step["nodes"]:
        node_copy = dict(node)
        if node_copy["id"] == new_node_id:
            node_copy["color"] = "#10b981"  # Emerald/green for the newly added node
            node_copy["size"] = 16
        elif node_copy["id"] == connected_to_id:
            node_copy["color"] = "#ef4444"  # Red for the node it connected to
            node_copy["size"] = 14
        else:
            node_copy["color"] = "#3b82f6"  # Blue for normal nodes
            node_copy["size"] = 11
        nodes.append(node_copy)

    edges = []
    for edge in step["edges"]:
        edge_copy = dict(edge)
        if (edge_copy["source"] == connected_to_id and edge_copy["target"] == new_node_id) or \
           (edge_copy["source"] == new_node_id and edge_copy["target"] == connected_to_id):
            edge_copy["color"] = "#f59e0b"  # Amber for the new edge
            edge_copy["width"] = 3
        else:
            edge_copy["color"] = "#cbd5e1"  # Slate-300 for existing edges
            edge_copy["width"] = 1.5
        edges.append(edge_copy)

    with growth_graph.hold_sync():
        growth_graph.nodes = nodes
        growth_graph.edges = edges
    return


@app.cell
def _(growth_graph, max_step, mo, step_index):
    mo.vstack(
        [
            mo.md(f"**Step:** `{step_index}` / `{max_step}`"),
            mo.md(f"**Selected nodes:** `{growth_graph.selected_nodes}`"),
            mo.md(f"**Selected edges:** `{growth_graph.selected_edges}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
