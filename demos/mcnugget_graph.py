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
    from collections import deque
    from pathlib import Path
    import sys

    import marimo as mo

    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import GraphWidget, PlaySlider

    return GraphWidget, PlaySlider, deque, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## McNugget sums

    Use the play slider to step through a breadth-first search of reachable totals.
    """)
    return


@app.cell
def _(mo):
    denominations_text = mo.ui.text(value="6, 9, 20", label="Box sizes")
    limit = mo.ui.slider(start=30, stop=500, step=5, value=80, label="Limit")
    color_arcs = mo.ui.checkbox(value=False, label="Color arcs by box size")
    color_nodes = mo.ui.checkbox(value=False, label="Color nodes by inbound arcs")
    mo.hstack([denominations_text, limit, color_arcs, color_nodes])
    return color_arcs, color_nodes, denominations_text, limit


@app.cell(hide_code=True)
def _(denominations_text):
    denominations = []
    for part in denominations_text.value.split(","):
        try:
            value = int(part.strip())
        except ValueError:
            continue
        if value > 0:
            denominations.append(value)
    if not denominations:
        denominations = [6, 9, 20]
    denominations = sorted(set(denominations))
    denominations
    return (denominations,)


@app.cell(hide_code=True)
def _(deque):
    def build_mcnugget_steps(denominations=(6, 9, 20), limit=60):
        queue = deque([0])
        visited = {0}
        visible_nodes = {0}
        visible_edges = []
        steps = [
            {
                "nodes": sorted(visible_nodes),
                "edges": list(visible_edges),
                "current": 0,
                "next": None,
                "box": None,
                "queue": list(queue),
            }
        ]

        while queue:
            current = queue.popleft()

            for box in denominations:
                next_total = current + box
                if next_total > limit:
                    continue

                visible_nodes.add(next_total)
                visible_edges.append((current, next_total, box))

                if next_total not in visited:
                    visited.add(next_total)
                    queue.append(next_total)

                steps.append(
                    {
                        "nodes": sorted(visible_nodes),
                        "edges": list(visible_edges),
                        "current": current,
                        "next": next_total,
                        "box": box,
                        "queue": list(queue),
                    }
                )

        return steps

    return (build_mcnugget_steps,)


@app.cell
def _(build_mcnugget_steps, denominations, limit):
    steps = build_mcnugget_steps(denominations=denominations, limit=limit.value)
    max_step = len(steps) - 1
    return max_step, steps


@app.cell
def _(PlaySlider, max_step, mo):
    play = mo.ui.anywidget(
        PlaySlider(
            min_value=0,
            max_value=max_step,
            step=1,
            interval_ms=200,
            loop=False,
        )
    )
    play
    return (play,)


@app.cell
def _(graph):
    graph
    return


@app.cell
def _(graph, mo, step):
    hovered = graph.hovered_node
    if hovered is None:
        path_md = "_Hover a node to see its shortest path from 0._"
    else:
        try:
            target = int(hovered)
        except (TypeError, ValueError):
            target = None

        parents = {}
        for src, dst, box in step["edges"]:
            if dst not in parents and dst != 0:
                parents[dst] = (src, box)

        if target is None:
            path_md = ""
        elif target == 0:
            path_md = "**Path to `0`:** `0` (start)"
        elif target not in parents:
            path_md = f"**Path to `{target}`:** not reachable yet."
        else:
            chain = []
            cur = target
            while cur in parents:
                src, box = parents[cur]
                chain.append((src, box, cur))
                cur = src
            chain.reverse()
            parts = [str(chain[0][0])]
            for src, box, dst in chain:
                parts.append(f"+{box}")
                parts.append(f"[{dst}]")
            path_md = f"**Path to `{target}`:** `" + " → ".join(parts) + "`"
    mo.md(path_md)
    return


@app.cell
def _(max_step, play, steps):
    step_index = int(play.value.get("value", 0))
    step_index = max(0, min(step_index, max_step))
    step = steps[step_index]
    return step, step_index


@app.cell
def _(GraphWidget, limit, mo):
    graph = mo.ui.anywidget(
        GraphWidget(
            nodes=list(range(limit.value + 1)),
            edges=[],
            directed=True,
            bounded=False,
            width=720,
            height=760,
        )
    )
    return (graph,)


@app.cell
def _(color_arcs, color_nodes, denominations, graph, limit, step):
    reachable = set(step["nodes"])
    indegree = {}
    for _src, _dst, _box in step["edges"]:
        indegree[_dst] = indegree.get(_dst, 0) + 1
    indeg_palette = ["#e2e8f0", "#bae6fd", "#7dd3fc", "#0ea5e9", "#0369a1", "#082f49"]

    def node_color(total):
        if color_nodes.value:
            deg = indegree.get(total, 0)
            return indeg_palette[min(deg, len(indeg_palette) - 1)]
        if total == 0:
            return "#7c3aed"
        if total in reachable:
            return "#334155"
        return "#cbd5e1"

    nodes = [
        {
            "name": total,
            "size": 12 if total == 0 else 7 + min(total / 16, 10),
            "color": node_color(total),
            "data": {
                "reachable": total in reachable,
                "in_degree": indegree.get(total, 0),
            },
        }
        for total in range(limit.value + 1)
    ]
    arc_palette = ["#0f766e", "#2563eb", "#dc2626", "#ca8a04", "#7c3aed", "#0891b2"]
    box_color = {
        box: arc_palette[i % len(arc_palette)] for i, box in enumerate(denominations)
    }
    edges = [
        {
            "source": source,
            "target": target,
            "name": f"+{box}",
            "color": box_color[box] if color_arcs.value else "#94a3b8",
        }
        for source, target, box in step["edges"]
    ]
    with graph.hold_sync():
        graph.nodes = nodes
        graph.edges = edges
    return


@app.cell
def _(limit, max_step, mo, step, step_index):
    if step["next"] is None:
        action = "Start at 0."
    else:
        action = f"From {step['current']}, add {step['box']} to reach {step['next']}."

    mo.vstack(
        [
            mo.md(f"**Step:** `{step_index}` / `{max_step}`"),
            mo.md(f"**Action:** {action}"),
            mo.md(f"**Reachable totals:** `{len(step['nodes'])}`"),
            mo.md(f"**Remaining queue:** `{step['queue'][:12]}`"),
            mo.md(
                f"**Missing totals so far:** `{[value for value in range(limit.value + 1) if value not in step['nodes']]}`"
            ),
        ]
    )
    return


@app.cell
def _(graph, mo):
    mo.vstack(
        [
            mo.md(f"**Selected totals:** `{graph.selected_nodes}`"),
            mo.md(f"**Selected additions:** `{graph.selected_edges}`"),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
