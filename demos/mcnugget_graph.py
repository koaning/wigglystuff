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
    limit = mo.ui.slider(start=30, stop=150, step=5, value=80, label="Limit")
    mo.hstack([denominations_text, limit])
    return denominations_text, limit


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
            interval_ms=500,
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
            height=460,
        )
    )
    return (graph,)


@app.cell
def _(denominations, graph, limit, step):
    reachable = set(step["nodes"])
    nodes = [
        {
            "name": total,
            "size": 12 if total == 0 else 7 + min(total / 16, 10),
            "color": (
                "#7c3aed"
                if total == 0
                else "#334155"
                if total in reachable
                else "#cbd5e1"
            ),
            "data": {"reachable": total in reachable},
        }
        for total in range(limit.value + 1)
    ]
    edges = [
        {
            "source": source,
            "target": target,
            "name": f"+{box}",
            "color": "#0f766e" if box == min(denominations) else "#2563eb",
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
