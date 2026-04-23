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
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import marimo as mo
    from wigglystuff import NestedTable

    return NestedTable, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # NestedTable

    Recursive expandable table for hierarchical data. Each row shows the
    node name followed by one column per value key, and optionally a
    share-of-root column next to each value.

    Leaves can carry a single number or a dict of `{column: number}` —
    the table auto-detects columns from the tree.
    """)
    return


@app.cell
def _(NestedTable, mo):
    tasks = {
        "analytics/cluster/Agglomerative": {"hours": 39.5, "count": 12},
        "analytics/cluster/Community": {"hours": 22.0, "count": 7},
        "analytics/graph/Shortest": {"hours": 32.75, "count": 9},
        "animate/Easing": {"hours": 84.0, "count": 24},
        "animate/Transitioner": {"hours": 102.25, "count": 31},
        "animate/Tween": {"hours": 29.0, "count": 8},
    }

    widget = mo.ui.anywidget(
        NestedTable.from_paths(
            tasks,
            root_name="projects",
            format={
                "hours": lambda v: f"{v:.1f}h",
                "count": lambda v: f"{int(v)}",
            },
            show_percent=["hours"],
            initial_expand_depth=2,
        )
    )
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    _rows = len(widget.expanded_paths)
    _sel = " / ".join(widget.selected_path) or "—"
    mo.md(f"Currently expanded rows: **{_rows}**. Last selected: **{_sel}**.")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Single value with `from_records`

    When the tree has scalar leaves the table shows one `Value` column.
    """)
    return


@app.cell
def _(NestedTable, mo):
    records_table = mo.ui.anywidget(
        NestedTable.from_records(
            [
                {"dept": "eng", "team": "infra", "hours": 40},
                {"dept": "eng", "team": "product", "hours": 70},
                {"dept": "design", "team": "brand", "hours": 55},
            ],
            path_cols=["dept", "team"],
            value_cols=["hours"],
            root_name="org",
            initial_expand_depth=1,
            format=lambda v: f"{v:.1f}h",
            show_percent=False,
        )
    )

    records_table
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## From a dataframe

    `from_dataframe` ducks-types pandas and polars — anything with a
    `.to_dicts()` or `.to_dict(orient="records")` method works. Pass a
    list for `value_col` to get a multi-column table.
    """)
    return


@app.cell
def _(NestedTable, mo):
    import polars as pl

    df = pl.DataFrame({
        "dept": ["eng", "eng", "eng", "eng", "design", "design"],
        "team": ["infra", "infra", "product", "product", "brand", "brand"],
        "person": ["alice", "bob", "carol", "dan", "erin", "fran"],
        "hours": [40, 35, 42, 28, 30, 25],
        "tickets": [12, 8, 15, 6, 9, 7],
    })
    df_table = mo.ui.anywidget(
        NestedTable.from_dataframe(
            df,
            path_cols=["dept", "team", "person"],
            value_cols=["tickets", "hours"],
            root_name="org",
            format={"hours": lambda v: f"{v:.0f}h"},
            show_percent=["hours"],
            initial_expand_depth=2,
        )
    )
    df_table
    return


if __name__ == "__main__":
    app.run()
