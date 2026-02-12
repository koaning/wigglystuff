# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "wigglystuff==0.2.18",
# ]
# ///

import marimo

__generated_with = "0.19.11"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartSelect

    return ChartSelect, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # ChartSelect Demo

    Interactive region selection for matplotlib charts.

    - Use **Box** or **Lasso** mode to draw a selection
    - Click and drag inside the selection to move it
    - Click outside the selection to clear it
    """)
    return


@app.cell
def _(np):
    np.random.seed(42)
    x_data = np.random.randn(300)
    y_data = np.random.randn(300)
    return x_data, y_data


@app.cell
def _(ChartSelect, x_data, y_data):
    def draw_chart(ax, widget):
        if widget.has_selection:
            mask = widget.get_mask(x_data, y_data)
            ax.scatter(
                x_data[~mask], y_data[~mask],
                alpha=0.3, color="gray", s=20
            )
            ax.scatter(
                x_data[mask], y_data[mask],
                alpha=0.8, color="#ef4444", s=40
            )
            ax.set_title(f"Selected: {mask.sum()} / {len(x_data)} points")
        else:
            ax.scatter(x_data, y_data, alpha=0.6, color="#3b82f6")
            ax.set_title("Draw a selection to highlight points")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(True, alpha=0.3)

    select = ChartSelect.from_callback(
        draw_fn=draw_chart,
        x_bounds=(-3.5, 3.5),
        y_bounds=(-3.5, 3.5),
        figsize=(5, 5),
        mode="box",
        selection_color="#ef4444",
    )
    return (select,)


@app.cell
def _(mo, select):
    widget = mo.ui.anywidget(select)
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget, x_data, y_data):
    _msg = "No selection yet"
    if widget.has_selection:
        _mask = widget.get_mask(x_data, y_data)
        _n = _mask.sum()
        if _n > 0:
            _msg = f"Selected {_n} points"
        else:
            _msg = "Selection contains 0 points"
    mo.callout(_msg)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Single-Mode Widgets

    You can restrict a widget to only one selection mode by passing `modes=["box"]` or `modes=["lasso"]`.
    When only one mode is available, the mode buttons are hidden.
    """)
    return


@app.cell
def _(ChartSelect, np):
    np.random.seed(123)
    _x = np.random.randn(150)
    _y = np.random.randn(150)

    def _draw_box(ax, widget):
        ax.scatter(_x, _y, alpha=0.6, color="#3b82f6", s=30)
        if widget.has_selection:
            mask = widget.get_mask(_x, _y)
            ax.scatter(_x[mask], _y[mask], alpha=0.9, color="#22c55e", s=50)
        ax.set_title("Box only")
        ax.grid(True, alpha=0.3)

    def _draw_lasso(ax, widget):
        ax.scatter(_x, _y, alpha=0.6, color="#3b82f6", s=30)
        if widget.has_selection:
            mask = widget.get_mask(_x, _y)
            ax.scatter(_x[mask], _y[mask], alpha=0.9, color="#f59e0b", s=50)
        ax.set_title("Lasso only")
        ax.grid(True, alpha=0.3)

    box_only = ChartSelect.from_callback(
        draw_fn=_draw_box,
        x_bounds=(-3, 3),
        y_bounds=(-3, 3),
        figsize=(4, 4),
        mode="box",
        modes=["box"],
        selection_color="#22c55e",
    )

    lasso_only = ChartSelect.from_callback(
        draw_fn=_draw_lasso,
        x_bounds=(-3, 3),
        y_bounds=(-3, 3),
        figsize=(4, 4),
        mode="lasso",
        modes=["lasso"],
        selection_color="#f59e0b",
    )
    return box_only, lasso_only


@app.cell
def _(box_only, lasso_only, mo):
    _box_widget = mo.ui.anywidget(box_only)
    _lasso_widget = mo.ui.anywidget(lasso_only)
    mo.hstack([_box_widget, _lasso_widget], justify="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Log-Scale Chart

    This section demonstrates ChartSelect on a chart with logarithmic axes.
    Draw a selection and check whether the correct points get highlighted.
    """)
    return


@app.cell
def _(np):
    np.random.seed(99)
    x_log = 10 ** (np.random.uniform(0, 3, 200))
    y_log = np.random.uniform(0, 10, 200)
    return x_log, y_log


@app.cell
def _(ChartSelect, x_log, y_log):
    def _draw_log(ax, widget):
        ax.set_xscale("log")
        if widget.has_selection:
            mask = widget.get_mask(x_log, y_log)
            ax.scatter(x_log[~mask], y_log[~mask], alpha=0.3, color="gray", s=20)
            ax.scatter(x_log[mask], y_log[mask], alpha=0.8, color="#ef4444", s=40)
            ax.set_title(f"Selected: {mask.sum()} / {len(x_log)} points")
        else:
            ax.scatter(x_log, y_log, alpha=0.6, color="#3b82f6")
            ax.set_title("Select points on log x-axis")
        ax.set_xlabel("X (log)")
        ax.set_ylabel("Y")
        ax.grid(True, alpha=0.3, which="both")

    log_select = ChartSelect.from_callback(
        draw_fn=_draw_log,
        x_bounds=(1, 1000),
        y_bounds=(0, 10),
        figsize=(5, 5),
        mode="box",
        selection_color="#ef4444",
    )
    return (log_select,)


@app.cell
def _(log_select, mo):
    log_widget = mo.ui.anywidget(log_select)
    return (log_widget,)


@app.cell
def _(log_widget):
    log_widget
    return


@app.cell
def _(log_widget, mo, x_log, y_log):
    _msg = "No selection yet (log chart)"
    if log_widget.has_selection:
        _mask = log_widget.get_mask(x_log, y_log)
        _n = _mask.sum()
        if _n > 0:
            _msg = f"Selected {_n} points (log chart)"
        else:
            _msg = "Selection contains 0 points (log chart)"
    mo.callout(_msg)
    return


if __name__ == "__main__":
    app.run()
