# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "matplotlib",
#     "wigglystuff==0.2.17",
# ]
# ///

import marimo

__generated_with = "0.19.5"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from wigglystuff import ChartPuck
    return ChartPuck, mo, np


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Greedy Sampled Search with Pucks

    Three pucks perform greedy sampled search on a 2D loss landscape with multiple local optima.
    Select a loss function from the dropdown and watch the pucks explore the space.
    """)
    return


@app.cell
def _(mo):
    # Loss function selection dropdown
    loss_functions = {
        "Rastrigin": "rastrigin",
        "Ackley": "ackley",
        "Rosenbrock": "rosenbrock",
        "Himmelblau": "himmelblau",
        "Multiple Peaks": "multiple_peaks",
        "Camel Back": "camel_back",
        "Beale": "beale",
        "Goldstein-Price": "goldstein_price",
        "Three Hump": "three_hump",
        "Levi": "levi",
        "Cross-in-Tray": "cross_in_tray",
    }
    loss_dropdown = mo.ui.dropdown(
        options=loss_functions,
        value="Rastrigin",  # Use display name as value
        label="Loss Function"
    )
    loss_dropdown
    return loss_dropdown, loss_functions


@app.cell
def _(mo):
    # Greedy search controls
    step_size_slider = mo.ui.slider(
        start=0.01,
        stop=1.5,
        value=0.1,
        step=0.01,
        label="Step Size"
    )
    population_size_slider = mo.ui.slider(
        start=5,
        stop=50,
        value=20,
        step=1,
        label="Population Size"
    )
    num_generations_slider = mo.ui.slider(
        start=10,
        stop=2000,
        value=100,
        step=10,
        label="Number of Generations"
    )
    _slider_display = mo.hstack([step_size_slider, population_size_slider, num_generations_slider], justify="start")
    _slider_display
    return num_generations_slider, population_size_slider, step_size_slider


@app.cell(hide_code=True)
def _(np):
    # Define loss functions with multiple local optima

    def rastrigin(x, y):
        """Rastrigin function - many local minima"""
        A = 10
        n = 2
        return A * n + (x**2 - A * np.cos(2 * np.pi * x)) + (y**2 - A * np.cos(2 * np.pi * y))

    def ackley(x, y):
        """Ackley function - many local minima"""
        a = 20
        b = 0.2
        c = 2 * np.pi
        term1 = -a * np.exp(-b * np.sqrt(0.5 * (x**2 + y**2)))
        term2 = -np.exp(0.5 * (np.cos(c * x) + np.cos(c * y)))
        return term1 + term2 + a + np.e

    def rosenbrock(x, y):
        """Rosenbrock function - narrow valley"""
        a = 1
        b = 100
        return (a - x)**2 + b * (y - x**2)**2

    def himmelblau(x, y):
        """Himmelblau's function - 4 equal minima"""
        return (x**2 + y - 11)**2 + (x + y**2 - 7)**2

    def multiple_peaks(x, y):
        """Custom function with multiple peaks"""
        return (
            3 * (1 - x)**2 * np.exp(-(x**2) - (y + 1)**2)
            - 10 * (x/5 - x**3 - y**5) * np.exp(-x**2 - y**2)
            - 1/3 * np.exp(-(x + 1)**2 - y**2)
        )

    def camel_back(x, y):
        """Six-hump camel back function - 6 local minima in symmetric pattern"""
        return (4 - 2.1*x**2 + x**4/3)*x**2 + x*y + (-4 + 4*y**2)*y**2

    def beale(x, y):
        """Beale function - long narrow curved valley"""
        return (1.5 - x + x*y)**2 + (2.25 - x + x*y**2)**2 + (2.625 - x + x*y**3)**2

    def goldstein_price(x, y):
        """Goldstein-Price function - multiple basins with ridges"""
        return (1 + (x + y + 1)**2 * (19 - 14*x + 3*x**2 - 14*y + 6*x*y + 3*y**2)) * \
               (30 + (2*x - 3*y)**2 * (18 - 32*x + 12*x**2 + 48*y - 36*x*y + 27*y**2))

    def three_hump(x, y):
        """Three-hump camel function - 3 local minima"""
        return 2*x**2 - 1.05*x**4 + x**6/6 + x*y + y**2

    def levi(x, y):
        """Levi function - wavy surface with many local minima"""
        return np.sin(3*np.pi*x)**2 + (x-1)**2 * (1 + np.sin(3*np.pi*y)**2) + (y-1)**2 * (1 + np.sin(2*np.pi*y)**2)

    def cross_in_tray(x, y):
        """Cross-in-tray function - cross-shaped pattern with multiple minima"""
        return -0.0001 * (np.abs(np.sin(x) * np.sin(y) * np.exp(np.abs(100 - np.sqrt(x**2 + y**2)/np.pi))) + 1)**0.1
    return (
        ackley,
        beale,
        camel_back,
        cross_in_tray,
        goldstein_price,
        himmelblau,
        levi,
        multiple_peaks,
        rastrigin,
        rosenbrock,
        three_hump,
    )


@app.cell(hide_code=True)
def _(
    ChartPuck,
    ackley,
    beale,
    camel_back,
    cross_in_tray,
    goldstein_price,
    himmelblau,
    levi,
    loss_dropdown,
    loss_functions,
    mo,
    multiple_peaks,
    np,
    num_generations_slider,
    population_size_slider,
    rastrigin,
    rosenbrock,
    step_size_slider,
    three_hump,
):
    # Create ChartPuck with callback to show loss landscape
    x_bounds = (-5, 5)
    y_bounds = (-5, 5)

    # Initial puck position (single puck)
    initial_x = [0.0]
    initial_y = [0.0]

    # Container to store loss function
    current_loss_fn = [None]

    # Get loss function based on dropdown
    # The dropdown value is the dict value (e.g., "rastrigin"), not the key
    loss_fn_name = loss_dropdown.value  # This is already the function name like "rastrigin"

    if loss_fn_name == "rastrigin":
        selected_loss_fn = rastrigin
    elif loss_fn_name == "ackley":
        selected_loss_fn = ackley
    elif loss_fn_name == "rosenbrock":
        selected_loss_fn = rosenbrock
    elif loss_fn_name == "himmelblau":
        selected_loss_fn = himmelblau
    elif loss_fn_name == "multiple_peaks":
        selected_loss_fn = multiple_peaks
    elif loss_fn_name == "camel_back":
        selected_loss_fn = camel_back
    elif loss_fn_name == "beale":
        selected_loss_fn = beale
    elif loss_fn_name == "goldstein_price":
        selected_loss_fn = goldstein_price
    elif loss_fn_name == "three_hump":
        selected_loss_fn = three_hump
    elif loss_fn_name == "levi":
        selected_loss_fn = levi
    elif loss_fn_name == "cross_in_tray":
        selected_loss_fn = cross_in_tray
    else:
        selected_loss_fn = rastrigin

    current_loss_fn[0] = selected_loss_fn

    def draw_loss_landscape(ax, widget):
        """Draw the loss landscape and greedy search trajectory."""
        loss_fn = current_loss_fn[0]

        # Access puck position from the widget parameter
        start_x = widget.x[0]
        start_y = widget.y[0]

        # Perform population-based greedy search starting from puck position
        step_size = step_size_slider.value
        population_size = int(population_size_slider.value)
        max_steps = int(num_generations_slider.value)  # Number of generations/populations

        # Store trajectory (best of each generation) for drawing lines
        trajectory_x = [start_x]
        trajectory_y = [start_y]

        # Store all population members for scatter plot
        all_population_x = []
        all_population_y = []

        current_x = start_x
        current_y = start_y

        # Perform population-based greedy search steps
        for step in range(max_steps):
            # Sample a population around current position
            population_x = []
            population_y = []
            population_losses = []

            for _ in range(population_size):
                # Sample uniformly in a circle around current position
                angle = np.random.uniform(0, 2 * np.pi)
                radius = np.random.uniform(0, step_size)
                sample_x = current_x + radius * np.cos(angle)
                sample_y = current_y + radius * np.sin(angle)

                # Keep within bounds
                sample_x = np.clip(sample_x, x_bounds[0], x_bounds[1])
                sample_y = np.clip(sample_y, y_bounds[0], y_bounds[1])

                # Evaluate loss
                sample_loss = loss_fn(sample_x, sample_y)

                population_x.append(sample_x)
                population_y.append(sample_y)
                population_losses.append(sample_loss)

            # Store all population members for scatter plot
            all_population_x.extend(population_x)
            all_population_y.extend(population_y)

            # Find best member of population
            best_idx = np.argmin(population_losses)
            best_x = population_x[best_idx]
            best_y = population_y[best_idx]
            best_loss = population_losses[best_idx]

            # If no improvement, stop searching
            current_loss = loss_fn(current_x, current_y)
            if best_loss >= current_loss:
                break

            # Move to best position and continue
            current_x = best_x
            current_y = best_y
            trajectory_x.append(current_x)
            trajectory_y.append(current_y)

        # Draw all population members as scatter
        if all_population_x:
            ax.scatter(all_population_x, all_population_y, c='blue', alpha=0.3, s=20, label='Population Samples')

        # Draw the search trajectory (best of each generation) as connected lines
        if len(trajectory_x) > 1:
            ax.plot(trajectory_x, trajectory_y, 'r-', linewidth=2, alpha=0.8, label='Best Path')
            ax.plot(trajectory_x, trajectory_y, 'ro', markersize=6, alpha=0.8)

        # Puck position (starting point) - don't change it
        puck_x = [start_x]
        puck_y = [start_y]

        ax.grid(True, alpha=0.3)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        # Get display name for title by reversing the lookup
        loss_fn_name_val = loss_dropdown.value
        display_name = next(k for k, v in loss_functions.items() if v == loss_fn_name_val)
        ax.set_title(f"Loss Landscape: {display_name}")

        # Create grid for loss visualization
        x_range = np.linspace(x_bounds[0], x_bounds[1], 200)
        y_range = np.linspace(y_bounds[0], y_bounds[1], 200)
        X, Y = np.meshgrid(x_range, y_range)

        # Compute loss at each point
        loss_values = loss_fn(X, Y)

        # Normalize for visualization
        loss_normalized = (loss_values - loss_values.min()) / (loss_values.max() - loss_values.min() + 1e-10)

        # Show loss landscape as heatmap
        im = ax.imshow(
            loss_normalized,
            extent=[x_bounds[0], x_bounds[1], y_bounds[0], y_bounds[1]],
            origin='lower',
            cmap='viridis_r',  # Reversed so low loss = bright
            aspect='equal',
            alpha=0.7,
            interpolation='bilinear'
        )

        # Draw contour lines
        levels = np.linspace(loss_values.min(), loss_values.max(), 15)
        ax.contour(X, Y, loss_values, levels=levels, colors='white', alpha=0.3, linewidths=0.5)

    # Create puck with callback
    puck = mo.ui.anywidget(
        ChartPuck.from_callback(
            draw_fn=draw_loss_landscape,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            figsize=(6, 6),  # Slightly smaller
            x=initial_x,
            y=initial_y,
            puck_radius=12,
            puck_color="#e63946",
        )
    )

    return (puck,)


@app.cell
def _(puck):
    puck
    return


@app.cell
def _(mo, puck):
    # Display puck coordinates
    mo.md(f"**Puck Position:** ({puck.x[0]:.2f}, {puck.y[0]:.2f})")
    return


if __name__ == "__main__":
    app.run()
