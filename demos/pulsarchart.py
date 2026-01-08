# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "matplotlib==3.10.8",
#     "numpy==2.4.0",
#     "pandas==2.3.3",
#     "wigglystuff==0.2.11",
# ]
# ///
import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    from wigglystuff import PulsarChart

    # Generate Joy Division-style pulsar data
    # The original is radio pulses from pulsar CP 1919 (PSR B1919+21)
    np.random.seed(42)
    n_rows = 50
    n_points = 300

    rows = []
    for j in range(n_rows):
        # Base line with small noise
        y = np.random.normal(0, 0.02, n_points)

        # Main pulse - a sharp peak that varies in shape per row
        pulse_center = n_points // 2 + np.random.randint(-10, 10)
        pulse_width = np.random.uniform(15, 25)
        pulse_height = np.random.uniform(0.4, 1.2)

        # Create pulse shape (combination of gaussians for irregular peaks)
        x = np.arange(n_points)
        pulse = pulse_height * np.exp(-((x - pulse_center) ** 2) / (2 * pulse_width ** 2))

        # Add secondary peaks for more interesting shape
        for _ in range(np.random.randint(1, 4)):
            offset = np.random.randint(-20, 20)
            width = np.random.uniform(5, 15)
            height = np.random.uniform(0.1, 0.5) * 10
            pulse += height * np.exp(-((x - pulse_center - offset) ** 2) / (2 * width ** 2))

        y += pulse
        rows.append(y)

    df = pd.DataFrame(rows)

    widget = mo.ui.anywidget(
        PulsarChart(
            df,
            width=400,
            height=600,
            overlap=0.85,
            stroke_width=1.0,
            peak_scale=2.5, 
            x_label="Pulse Phase",
            y_label="Pulse Number", 
        )
    )
    return mo, widget


@app.cell
def _():
    # widget
    return


@app.cell
def _(mo, widget):
    mo.callout(
        f"Selected Index: {widget.selected_index}, Row Length: {len(widget.selected_row) if widget.selected_row else 0}"
    )
    return


@app.cell
def _(widget):
    import matplotlib.pyplot as plt

    def make_plot(selected_row):
        if not selected_row:
            return None
        fig, ax = plt.subplots(figsize=(5, 5))
        xs = [p["x"] for p in selected_row]
        ys = [p["y"] for p in selected_row]
        ax.plot(xs, ys)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        plt.close(fig)
        return fig

    plot = make_plot(widget.value.get("selected_row"))
    return (plot,)


@app.cell
def _(mo, plot, widget):
    mo.hstack([
        widget, 
        plot
    ], align="start")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
