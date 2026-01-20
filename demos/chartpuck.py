import marimo

__generated_with = "0.18.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck

    return ChartPuck, mo, np, plt


@app.cell
def _(ChartPuck, np, plt):
    # Create a scatter plot
    np.random.seed(42)
    x_data = np.random.randn(50)
    y_data = np.random.randn(50)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x_data, y_data, alpha=0.6)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Drag the puck to select coordinates")
    ax.grid(True, alpha=0.3)

    puck = ChartPuck(fig, x=0, y=0)
    plt.close(fig)
    return ax, fig, puck, x_data, y_data


@app.cell
def _(mo, puck):
    widget = mo.ui.anywidget(puck)
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(mo, widget):
    mo.callout(f"Selected position: x = {widget.x:.3f}, y = {widget.y:.3f}")
    return


if __name__ == "__main__":
    app.run()
