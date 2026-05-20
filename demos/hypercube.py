# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "wigglystuff==0.5.1",
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
    ## Hypercube $Q_n$

    Every vertex is a binary string of length $n$; two vertices are connected
    when they differ in exactly one bit. Because every vertex has the same
    degree and the graph is perfectly symmetric, the force layout unfurls it:
    $Q_3$ snaps into a cube, $Q_4$ projects into a tesseract (cube within a
    cube), and so on.

    Nodes are colored by popcount (number of 1 bits); edges are colored by
    which bit position the endpoints differ in.
    """)
    return


@app.cell
def _(mo):
    dim = mo.ui.slider(start=1, stop=6, step=1, value=3, label="Dimension n")
    node_size = mo.ui.slider(start=2, stop=14, step=1, value=10, label="Node size")
    mo.hstack([dim, node_size])
    return dim, node_size


@app.cell
def _():
    NODE_PALETTE = [
        "#1e40af",
        "#3b82f6",
        "#06b6d4",
        "#10b981",
        "#f59e0b",
        "#f97316",
        "#dc2626",
    ]
    EDGE_PALETTE = [
        "#ef4444",
        "#f59e0b",
        "#10b981",
        "#3b82f6",
        "#8b5cf6",
        "#ec4899",
    ]

    def build_hypercube(n, size_px=10):
        size = 1 << n
        nodes = []
        for i in range(size):
            label = format(i, f"0{n}b") if n > 0 else "0"
            popcount = bin(i).count("1")
            nodes.append(
                {
                    "id": label,
                    "name": label,
                    "color": NODE_PALETTE[popcount % len(NODE_PALETTE)],
                    "size": size_px,
                }
            )

        edges = []
        for i in range(size):
            label_i = format(i, f"0{n}b") if n > 0 else "0"
            for bit in range(n):
                j = i ^ (1 << bit)
                if i < j:
                    label_j = format(j, f"0{n}b")
                    edges.append(
                        {
                            "source": label_i,
                            "target": label_j,
                            "color": EDGE_PALETTE[bit % len(EDGE_PALETTE)],
                            "width": 1.5,
                        }
                    )
        return nodes, edges

    return (build_hypercube,)


@app.cell
def _(GraphWidget, mo):
    hypercube = mo.ui.anywidget(
        GraphWidget(
            nodes=[],
            edges=[],
            directed=False,
            bounded=False,
            width=720,
            height=520,
        )
    )
    hypercube
    return (hypercube,)


@app.cell
def _(build_hypercube, dim, hypercube, node_size):
    _nodes, _edges = build_hypercube(dim.value, size_px=node_size.value)
    with hypercube.hold_sync():
        hypercube.nodes = _nodes
        hypercube.edges = _edges
    return


@app.cell
def _(dim, hypercube, mo):
    _n = dim.value
    _v = 1 << _n
    _e = _n * (1 << (_n - 1)) if _n > 0 else 0
    mo.vstack(
        [
            mo.md(f"**n:** `{_n}` &nbsp;&nbsp; **|V|:** `{_v}` &nbsp;&nbsp; **|E|:** `{_e}`"),
            mo.md(f"**Hovered node:** `{hypercube.hovered_node}`"),
            mo.md(f"**Selected nodes:** `{hypercube.selected_nodes}`"),
            mo.md(f"**Selected edges:** `{hypercube.selected_edges}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
