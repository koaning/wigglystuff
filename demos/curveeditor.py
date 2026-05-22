import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import CurveEditor

    editor = mo.ui.anywidget(
        CurveEditor(
            curve="natural",
            loop=True,
            width=450,
            height=450,
            sync_throttle_ms=250,
            points=[
                {"x": 0.0, "y": 0.12},
                {"x": 0.15, "y": 0.32},
                {"x": 0.35, "y": 0.78},
                {"x": 0.55, "y": 0.44},
                {"x": 0.78, "y": 0.86},
                {"x": 1.0, "y": 0.55},
            ],
        )
    )
    return editor, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## CurveEditor

    Edit chart-space knots and switch between D3 curve interpolators.
    Use the progress control to emit the current path position as `x` and `y`.
    Set `sync_throttle_ms` on construction to control how often playback syncs
    those values back to Python.
    """)
    return


@app.cell
def _(editor):
    editor
    return


@app.cell
def _(editor, mo):
    selected = (
        editor.points[editor.selected_index]
        if 0 <= editor.selected_index < len(editor.points)
        else None
    )
    mo.callout(
        f"curve = {editor.curve}; t = {editor.t:.3f}; "
        f"current = ({editor.x:.3f}, {editor.y:.3f}); {len(editor.points)} knots; "
        f"sync throttle = {editor.widget.sync_throttle_ms} ms; "
        f"selected = {selected if selected is not None else 'none'}"
    )
    return


if __name__ == "__main__":
    app.run()
