# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "scikit-learn",
#     "scipy",
#     "wigglystuff==0.2.17",
# ]
# ///

import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck
    return ChartPuck, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Single Puck
    """)
    return


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
    return (puck,)


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
    mo.callout(f"Selected position: x = {widget.x[0]:.3f}, y = {widget.y[0]:.3f}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Multiple Pucks
    """)
    return


@app.cell
def _(ChartPuck, np, plt):
    # Create a scatter plot with multiple pucks
    np.random.seed(123)
    x_multi = np.random.randn(50)
    y_multi = np.random.randn(50)

    fig2, ax2 = plt.subplots(figsize=(6, 6))
    ax2.scatter(x_multi, y_multi, alpha=0.6)
    ax2.set_xlim(-3, 3)
    ax2.set_ylim(-3, 3)
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_title("Drag any puck - closest one will move")
    ax2.grid(True, alpha=0.3)

    multi_puck = ChartPuck(
        fig2,
        x=[-1.5, 0, 1.5],
        y=[-1.5, 0, 1.5],
        puck_color="#2196f3",
    )
    plt.close(fig2)
    return (multi_puck,)


@app.cell
def _(mo, multi_puck):
    multi_widget = mo.ui.anywidget(multi_puck)
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_widget
    return


@app.cell
def _(mo, multi_widget):
    positions = [
        f"Puck {i+1}: ({x:.2f}, {y:.2f})"
        for i, (x, y) in enumerate(zip(multi_widget.x, multi_widget.y))
    ]
    mo.callout("\n".join(positions))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Dynamic Chart Updates
    """)
    return


@app.cell
def _(np):
    np.random.seed(42)
    dynamic_data_x = np.random.randn(50)
    dynamic_data_y = np.random.randn(50)
    return dynamic_data_x, dynamic_data_y


@app.cell
def _(ChartPuck, dynamic_data_x, dynamic_data_y):
    def draw_with_crosshairs(ax, widget):
        x, y = widget.x[0], widget.y[0]
        ax.scatter(dynamic_data_x, dynamic_data_y, alpha=0.6)
        ax.axvline(x, color="red", linestyle="--", alpha=0.7)
        ax.axhline(y, color="red", linestyle="--", alpha=0.7)
        ax.set_title(f"Position: ({x:.2f}, {y:.2f})")
        ax.grid(True, alpha=0.3)


    dynamic_puck = ChartPuck.from_callback(
        draw_fn=draw_with_crosshairs,
        x_bounds=(-3, 3),
        y_bounds=(-3, 3),
        figsize=(6, 6),
        x=0,
        y=0,
        puck_color="#4caf50",
    )
    return (dynamic_puck,)


@app.cell
def _(dynamic_puck, mo):
    dynamic_widget = mo.ui.anywidget(dynamic_puck)
    return (dynamic_widget,)


@app.cell
def _(dynamic_widget):
    dynamic_widget
    return


@app.cell
def _(dynamic_widget, mo):
    mo.callout(f"Dynamic position: x = {dynamic_widget.x[0]:.3f}, y = {dynamic_widget.y[0]:.3f}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Spline Curve Editor

    Drag the pucks to shape a curve. The spline interpolates through all control points,
    with fixed anchors at (-3, 0) and (3, 1) shown as black dots.
    Use the slider to change the number of pucks, and the dropdown to select the interpolation method.
    """)
    return


@app.cell
def _(mo):
    n_pucks_slider = mo.ui.slider(3, 8, value=5, label="Number of pucks")
    return (n_pucks_slider,)


@app.cell
def _(ChartPuck, n_pucks_slider, np):
    from scipy.interpolate import CubicSpline, PchipInterpolator, Akima1DInterpolator, interp1d, BarycentricInterpolator

    # Internal state for interpolation method (not a marimo dependency)
    method_state = {"value": "CubicSpline"}

    def draw_spline_chart(ax, x_pucks, y_pucks, method):
        # Add fixed anchor points at (-3, 0) and (3, 1)
        x_all = np.concatenate([[-3], x_pucks, [3]])
        y_all = np.concatenate([[0], y_pucks, [1]])

        # Sort points by x for proper spline fitting
        sorted_indices = np.argsort(x_all)
        x_sorted = x_all[sorted_indices]
        y_sorted = y_all[sorted_indices]

        # Ensure strictly increasing x by adding small perturbations to duplicates
        for i in range(1, len(x_sorted)):
            if x_sorted[i] <= x_sorted[i - 1]:
                x_sorted[i] = x_sorted[i - 1] + 1e-6

        # Create dense x values for smooth curve
        x_dense = np.linspace(-3, 3, 200)

        # Select interpolation method
        if method == "CubicSpline":
            spline = CubicSpline(x_sorted, y_sorted)
        elif method == "Pchip":
            spline = PchipInterpolator(x_sorted, y_sorted)
        elif method == "Akima":
            spline = Akima1DInterpolator(x_sorted, y_sorted)
        elif method == "Linear":
            spline = interp1d(x_sorted, y_sorted, kind="linear", fill_value="extrapolate")
        elif method == "Quadratic":
            spline = interp1d(x_sorted, y_sorted, kind="quadratic", fill_value="extrapolate")
        elif method == "Step":
            spline = interp1d(x_sorted, y_sorted, kind="zero", fill_value="extrapolate")
        elif method == "Nearest":
            spline = interp1d(x_sorted, y_sorted, kind="nearest", fill_value="extrapolate")
        else:  # Barycentric
            spline = BarycentricInterpolator(x_sorted, y_sorted)

        y_dense = spline(x_dense)

        # Plot the spline curve
        ax.plot(x_dense, y_dense, "b-", linewidth=2)
        ax.set_xlim(-3, 3)
        ax.set_ylim(-0.1, 1.1)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title(f"Spline Curve ({method})")
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.axhline(1, color="gray", linewidth=0.5)
        # Mark fixed anchor points
        ax.plot([-3, 3], [0, 1], "ko", markersize=8, zorder=5)

    def draw_spline(ax, widget):
        draw_spline_chart(ax, list(widget.x), list(widget.y), method_state["value"])

    # Initial puck positions: evenly spaced between anchors (excluding -3 and 3)
    _n = n_pucks_slider.value
    _init_x = np.linspace(-2.5, 2.5, _n).tolist()
    _init_y = np.linspace(0.1, 0.9, _n).tolist()

    spline_puck = ChartPuck.from_callback(
        draw_fn=draw_spline,
        x_bounds=(-3, 3),
        y_bounds=(-0.1, 1.1),
        figsize=(6, 4),
        x=_init_x,
        y=_init_y,
        puck_color="#9c27b0",
        drag_y_bounds=(0, 1),
    )
    return method_state, spline_puck


@app.cell
def _(method_state, mo, n_pucks_slider, spline_puck):
    def on_method_change(new_val):
        method_state["value"] = new_val
        spline_puck.redraw()

    spline_method = mo.ui.dropdown(
        options=["CubicSpline", "Pchip", "Akima", "Linear", "Quadratic", "Step", "Nearest", "Barycentric"],
        value=method_state["value"],
        label="Interpolation method",
        on_change=on_method_change,
    )
    mo.hstack([n_pucks_slider, spline_method], gap=2)
    return


@app.cell
def _(mo, spline_puck):
    spline_widget = mo.ui.anywidget(spline_puck)
    return (spline_widget,)


@app.cell
def _(spline_widget):
    spline_widget
    return


@app.cell
def _(mo, spline_widget):
    _positions = [f"({x:.2f}, {y:.2f})" for x, y in zip(spline_widget.x, spline_widget.y)]
    mo.callout(f"Control points: {', '.join(_positions)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Interactive K-Means Clustering

    Drag the 10 pucks to explore how cluster centroids affect digit classification.
    The chart below shows the nearest digit images to each puck position.
    """)
    return


@app.cell
def _(mo):
    run_kmeans_button = mo.ui.run_button(label="Load K-Means Demo")
    run_kmeans_button
    return (run_kmeans_button,)


@app.cell
def _(mo, run_kmeans_button):
    mo.stop(
        not run_kmeans_button.value,
        mo.md("*Click the button above to load the interactive k-means demo.*"),
    )

    from sklearn.datasets import load_digits
    from sklearn.decomposition import PCA

    # Load digits dataset and reduce to 2D
    digits = load_digits()
    reduced_data = PCA(n_components=2).fit_transform(digits.data)

    # Compute bounds with padding
    x_min, x_max = reduced_data[:, 0].min() - 1, reduced_data[:, 0].max() + 1
    y_min, y_max = reduced_data[:, 1].min() - 1, reduced_data[:, 1].max() + 1
    return digits, reduced_data, x_max, x_min, y_max, y_min


@app.cell
def _(ChartPuck, np, plt, reduced_data, x_max, x_min, y_max, y_min):
    from sklearn.cluster import KMeans

    def draw_kmeans(ax, widget):
        centroids = list(zip(widget.x, widget.y))

        h = 0.3  # mesh step size
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

        # Create KMeans with our centroids
        kmeans = KMeans(
            n_clusters=len(centroids),
            init=np.array(centroids),
            n_init=1,
            max_iter=1,  # Just use our centroids, don't iterate
        )
        kmeans.fit(reduced_data)

        # Predict on mesh
        Z = kmeans.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)

        # Draw decision boundaries
        ax.imshow(
            Z,
            interpolation="nearest",
            extent=(xx.min(), xx.max(), yy.min(), yy.max()),
            cmap=plt.cm.tab10,
            aspect="auto",
            origin="lower",
            alpha=0.6,
        )

        # Draw data points
        ax.plot(reduced_data[:, 0], reduced_data[:, 1], "k.", markersize=2)

        # Draw centroids with cluster numbers
        centroids_arr = np.array(centroids)
        for i, (cx, cy) in enumerate(centroids_arr):
            ax.scatter(cx, cy, marker="o", s=200, c="white", edgecolors="black", zorder=10)
            ax.text(
                cx, cy, str(i), ha="center", va="center", fontsize=10, fontweight="bold", zorder=11
            )

        ax.set_title("Drag pucks to move cluster centroids")

    # Initial centroid positions (spread in a grid pattern)
    init_x = [-30, -15, 0, 15, 30, -30, -15, 0, 15, 30]
    init_y = [-20, -20, -20, -20, -20, 20, 20, 20, 20, 20]

    kmeans_puck = ChartPuck.from_callback(
        draw_fn=draw_kmeans,
        x_bounds=(x_min, x_max),
        y_bounds=(y_min, y_max),
        figsize=(6, 5),
        x=init_x,
        y=init_y,
        puck_color="#e63946",
        puck_radius=8,
    )
    return (kmeans_puck,)


@app.cell
def _(kmeans_puck, mo):
    kmeans_widget = mo.ui.anywidget(kmeans_puck)
    return (kmeans_widget,)


@app.cell
def _(digits, kmeans_widget, mo, np, plt, reduced_data):
    def get_nearest_digits(centroids, reduced_data, digits, n_nearest=5):
        """Find the n nearest digit images to each centroid."""
        nearest_per_centroid = []
        for cx, cy in centroids:
            distances = np.sqrt((reduced_data[:, 0] - cx) ** 2 + (reduced_data[:, 1] - cy) ** 2)
            nearest_indices = np.argsort(distances)[:n_nearest]
            nearest_per_centroid.append(nearest_indices)
        return nearest_per_centroid


    # Get current puck positions as centroids
    centroids = list(zip(kmeans_widget.x, kmeans_widget.y))
    nearest_indices = get_nearest_digits(centroids, reduced_data, digits, n_nearest=5)

    # Create a figure showing nearest digits for each puck
    fig_digits, axes = plt.subplots(10, 5, figsize=(4, 8))
    fig_digits.suptitle("Nearest digits to each puck", fontsize=10)

    for puck_idx, indices in enumerate(nearest_indices):
        for col_idx, digit_idx in enumerate(indices):
            _ax = axes[puck_idx, col_idx]
            _ax.imshow(digits.images[digit_idx], cmap="gray_r")
            _ax.axis("off")
            if col_idx == 0:
                _ax.set_title(f"{puck_idx}", fontsize=8, loc="left")

    plt.tight_layout()

    # Display both charts side by side
    mo.hstack([kmeans_widget, fig_digits], justify="center", gap=2)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Export to scikit-learn

    Use `export_kmeans()` to get a scikit-learn KMeans instance with your puck positions as initial centroids:
    """)
    return


@app.cell
def _(kmeans_widget):
    # Export puck positions as a KMeans estimator
    kmeans_estimator = kmeans_widget.export_kmeans()
    print(f"KMeans with {kmeans_estimator.n_clusters} clusters")
    print(f"Initial centroids:\n{kmeans_estimator.init}")
    return


if __name__ == "__main__":
    app.run()
