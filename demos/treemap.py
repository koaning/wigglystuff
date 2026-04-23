# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.7",
#     "polars",
#     "wigglystuff==0.3.1",
# ]
# ///

import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import Treemap

    return Treemap, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Treemap

    A zoomable hierarchical treemap. Click a rectangle to zoom in; click
    the breadcrumb to zoom back out.

    Leaves can carry a single number or a dict of `{column: number}`. When
    values are dicts, pass `value_col` to pick which column drives rectangle
    sizing, and use `format=` to humanize the label.
    """)
    return


@app.cell
def _(Treemap, mo):
    tasks = {
        "analytics/cluster/Agglomerative": {"hours": 39.5, "count": 12},
        "analytics/cluster/Community": {"hours": 22.0, "count": 7},
        "analytics/cluster/Hierarchical": {"hours": 48.25, "count": 18},
        "analytics/graph/Betweenness": {"hours": 18.0, "count": 4},
        "analytics/graph/MaxFlow": {"hours": 56.5, "count": 15},
        "analytics/graph/Shortest": {"hours": 32.75, "count": 9},
        "animate/Easing": {"hours": 84.0, "count": 24},
        "animate/Transition": {"hours": 41.5, "count": 11},
        "animate/Transitioner": {"hours": 102.25, "count": 31},
        "animate/Tween": {"hours": 29.0, "count": 8},
        "data/converters/JSONConverter": {"hours": 22.5, "count": 6},
    }

    widget = mo.ui.anywidget(
        Treemap.from_paths(
            tasks,
            value_col="hours",
            format=lambda v: f"{v:.1f}h",
            root_name="projects",
            width="100%"
        )
    )
    widget
    return (widget,)


@app.cell(hide_code=True)
def _(mo, widget):
    mo.md(f"""
    Currently zoomed into: **{' / '.join(widget.selected_path) or '—'}**
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Simulated deep hierarchy

    A synthetic tree generated with `random`, branching up to eight levels
    deep with variable fan-out. Click a rectangle to zoom one level in;
    the breadcrumb walks you back out. Pass `palette=[...]` to colorize
    the top-level groups.
    """)
    return


@app.cell
def _(Treemap, mo):
    import random

    rng = random.Random(42)
    paths: dict[str, int] = {}

    def walk(depth_left: int, parts: list[str]) -> None:
        if depth_left == 0 or (depth_left < 6 and rng.random() < 0.25):
            paths["/".join(parts)] = rng.randint(50, 2500)
            return
        for i in range(rng.randint(2, 4)):
            walk(depth_left - 1, parts + [chr(ord("a") + i)])

    walk(8, [])

    deep_widget = mo.ui.anywidget(
        Treemap.from_paths(paths, root_name="fs", width="100%")
    )
    deep_widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## From a dataframe

    `from_dataframe` ducks-types pandas and polars. When `value_col` is a
    list, the first entry drives rectangle sizing.
    """)
    return


@app.cell
def _(Treemap, mo):
    import polars as pl

    df = pl.DataFrame({
        "dept": ["eng", "eng", "eng", "eng", "design", "design"],
        "team": ["infra", "infra", "product", "product", "brand", "brand"],
        "person": ["alice", "bob", "carol", "dan", "erin", "fran"],
        "hours": [40, 35, 42, 28, 30, 25],
        "tickets": [12, 8, 15, 6, 9, 7],
    })
    df_widget = mo.ui.anywidget(
        Treemap.from_dataframe(
            df,
            path_cols=["dept", "team", "person"],
            value_cols=["hours", "tickets"],
            root_name="org",
            format=lambda v: f"{v:.0f}h",
            width=800,
        )
    )
    df_widget
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Real pytest durations

    Loads a `pytest --report-log` JSONL from scikit-lego's test suite and
    builds a treemap of test durations. Slow spots become visually
    dominant. The `::` separator in pytest node ids is rewritten to `/`
    so each test function becomes its own leaf.
    """)
    return


@app.cell
def _(Treemap, mo):
    import json
    import urllib.request

    url = (
        "https://raw.githubusercontent.com/koaning/"
        "pytest-duration-insights/refs/heads/main/"
        "tests/data/scikit-lego-reportlog.jsonl"
    )
    with urllib.request.urlopen(url) as resp:
        lines = resp.read().decode().splitlines()

    durations: dict[str, float] = {}
    for line in lines:
        row = json.loads(line)
        nid = row.get("nodeid")
        if not nid:
            continue
        dur = row.get("duration")
        if dur is None:
            continue
        path = nid.replace("::", "/").removeprefix("tests/")
        durations[path] = durations.get(path, 0.0) + dur

    pytest_widget = mo.ui.anywidget(
        Treemap.from_paths(
            durations,
            root_name="tests",
            format=lambda v: f"{v:.2f}s",
            width="100%",
        )
    )
    pytest_widget
    return


if __name__ == "__main__":
    app.run()
