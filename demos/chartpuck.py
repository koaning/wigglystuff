# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.19.6",
#     "matplotlib==3.10.8",
#     "numpy==2.4.1",
#     "scikit-learn==1.8.0",
#     "scipy==1.17.0",
#     "wigglystuff==0.2.16",
# ]
# ///
import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


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
    def draw_with_crosshairs(ax, x, y):
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
    spline_method = mo.ui.dropdown(
        options=["CubicSpline", "Pchip", "Akima", "Linear"],
        value="CubicSpline",
        label="Interpolation method",
    )
    mo.hstack([n_pucks_slider, spline_method], gap=2)
    return n_pucks_slider, spline_method


@app.cell
def _(ChartPuck, n_pucks_slider, np, plt, spline_method):
    from scipy.interpolate import CubicSpline, PchipInterpolator, Akima1DInterpolator, interp1d
    from wigglystuff.chart_puck import fig_to_base64

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
        else:  # Linear
            spline = interp1d(x_sorted, y_sorted, kind="linear", fill_value="extrapolate")

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

    # Initial puck positions: evenly spaced between anchors (excluding -3 and 3)
    _n = n_pucks_slider.value
    _init_x = np.linspace(-2.5, 2.5, _n).tolist()
    _init_y = np.linspace(0.1, 0.9, _n).tolist()

    # Create initial figure
    _fig, _ax = plt.subplots(figsize=(6, 4))
    draw_spline_chart(_ax, _init_x, _init_y, spline_method.value)

    spline_puck = ChartPuck(
        _fig,
        x=_init_x,
        y=_init_y,
        puck_color="#9c27b0",
        drag_y_bounds=(0, 1),  # Constrain y to valid spline range
    )
    plt.close(_fig)

    # Observer to redraw spline when pucks move
    def on_spline_change(change):
        _fig_update, _ax_update = plt.subplots(figsize=(6, 4))
        draw_spline_chart(_ax_update, list(spline_puck.x), list(spline_puck.y), spline_method.value)
        spline_puck.chart_base64 = fig_to_base64(_fig_update)
        plt.close(_fig_update)

    spline_puck.observe(on_spline_change, names=["x", "y"])
    return (spline_puck,)


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
    def draw_kmeans_boundaries(ax, centroids, reduced_data, x_min, x_max, y_min, y_max):
        from sklearn.cluster import KMeans

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
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)


    # Initial centroid positions (spread in a grid pattern)
    init_x = [-30, -15, 0, 15, 30, -30, -15, 0, 15, 30]
    init_y = [-20, -20, -20, -20, -20, 20, 20, 20, 20, 20]

    # Create initial figure
    fig_km, ax_km = plt.subplots(figsize=(6, 5))
    initial_centroids = list(zip(init_x, init_y))
    draw_kmeans_boundaries(ax_km, initial_centroids, reduced_data, x_min, x_max, y_min, y_max)

    # Create widget with 10 pucks (one for each digit)
    kmeans_puck = ChartPuck(
        fig_km,
        x=init_x,
        y=init_y,
        puck_color="#e63946",
        puck_radius=8,
    )
    plt.close(fig_km)


    # Set up observer to redraw on puck movement
    def on_kmeans_change(change):
        fig_update, ax_update = plt.subplots(figsize=(6, 5))
        centroids = list(zip(kmeans_puck.x, kmeans_puck.y))
        draw_kmeans_boundaries(ax_update, centroids, reduced_data, x_min, x_max, y_min, y_max)
        from wigglystuff.chart_puck import fig_to_base64

        kmeans_puck.chart_base64 = fig_to_base64(fig_update)
        plt.close(fig_update)


    kmeans_puck.observe(on_kmeans_change, names=["x", "y"])
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
