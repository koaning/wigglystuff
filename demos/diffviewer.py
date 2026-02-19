import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## DiffViewer

    A rich file diff viewer powered by `@pierre/diffs`. Supports split and unified diff styles with syntax highlighting.
    """)
    return


@app.cell
def _():
    expected = {"items": [{"name": "Espresso", "size": "Trenta", "quantity": 1, "modifiers": ["Oat Milk"]}, {"name": "Earl Grey Tea", "size": "Tall", "quantity": 1, "modifiers": []}, {"name": "Cold Brew", "size": "Tall", "quantity": 2, "modifiers": ["Breve"]}], "total_price": 18.4}

    out = {"items": [{"name": "Espresso", "size": "Trenta", "quantity": 1, "modifiers": ["Oat Milk"]}, {"name": "Earl Grey Tea", "size": "Tall", "quantity": 1, "modifiers": []}, {"name": "Cold Brew", "size": "Tall", "quantity": 2, "modifiers": ["Breve"]}], "total_price": 184}
    return expected, out


@app.cell
def _(expected, mo, out):
    import json
    from wigglystuff import DiffViewer

    widget = mo.ui.anywidget(
        DiffViewer(
            old_name="expected.json",
            old_contents=json.dumps(expected, indent=2) + "\n",
            new_name="received.json",
            new_contents=json.dumps(out, indent=2) + "\n",
            diff_style="split",
            expand_unchanged=True,
        )
    )
    widget
    return (DiffViewer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Unified View

    Set `diff_style="unified"` for a single-column view.
    """)
    return


@app.cell
def _(DiffViewer, mo):
    unified = mo.ui.anywidget(DiffViewer(
        old_name="config.json",
        old_contents='{\n  "debug": false,\n  "port": 3000\n}\n',
        new_name="config.json",
        new_contents='{\n  "debug": true,\n  "port": 8080,\n  "host": "0.0.0.0"\n}\n',
        diff_style="unified",
    ))
    unified
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
