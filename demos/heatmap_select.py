# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "wigglystuff==0.5.23",
# ]
# ///

import marimo

__generated_with = "0.23.15"
app = marimo.App()


@app.cell
def _():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    import marimo as mo
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import Normalize, PowerNorm
    from wigglystuff import HeatmapSelect, Hint

    return HeatmapSelect, Hint, Normalize, PowerNorm, matplotlib, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # HeatmapSelect

    A parameter space, in the spirit of Bret Victor's
    [*Up and Down the Ladder of Abstraction*](https://worrydream.com/LadderOfAbstraction/).

    One pixel is one cell, and the two strips along the left and bottom edges of
    the grid are interactive gutters.

    - **Hover the grid** to preview a single cell. Hover the **left gutter** for a
      whole row, or the **bottom gutter** for a whole column.
    - **Click** to pin. The three pins are **independent and coexist** — pin a
      cell, then a row, then a column, and all three stay. Clicking a region only
      replaces that region's pin; hovering never disturbs any of them.
    - **Double-click** a region to drop just that pin.

    Each axis has its own colour, in the widget's bands *and* in the charts beside
    them: <span style="color:#1f4fd8">**blue** for the y axis</span> (a row) and
    <span style="color:#e07b00">**orange** for the x axis</span> (a column).
    Hovering draws faint and transparent; pinning makes it solid. Making sense of
    a *combination* of pins is the caller's job, not the widget's.

    Below are two parameter spaces that want completely different things from you.
    The first is smooth enough that you can read conclusions straight off it. The
    second is chaotic, and poking at it is the only thing you can do.
    """)
    return


@app.cell
def _():
    # Shared by both examples, and by both sets of charts, so that "blue means the
    # y axis" is true everywhere on this page. ROW comes off the y axis, COL off
    # the x axis.
    ROW_COLOR = "#1f4fd8"
    COL_COLOR = "#e07b00"
    CELL_COLOR = "#111111"
    return CELL_COLOR, COL_COLOR, ROW_COLOR


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. A field you can read — a cannon's range

    One cell is one cannon shot. **The x axis is the angle you fire at, the y axis
    is how fast the ball leaves the barrel**, and the grid is coloured by **how far
    downrange the ball lands** — dark is a short shot, bright is a long one. There
    is quadratic air drag, and the `wind` slider blows horizontally.

    The field is smooth, so unlike the pendulum below, the picture supports actual
    conclusions. Pin the top row and the fan of arcs has one clear best angle: at
    60 m/s in still air it is **42°**, not the 45° you would get in a vacuum,
    because drag punishes the longer flight time. Drag the wind up to a tailwind
    and it walks back toward 45°.
    """)
    return


@app.cell
def _(np):
    # 91 columns x 100 rows, matching Victor's grid shape.
    ANGLES = np.linspace(0.0, 90.0, 91)  # degrees
    SPEEDS = np.linspace(5.0, 60.0, 100)  # m/s
    GRAVITY = 9.81
    DRAG = 0.002  # quadratic drag, 1/m
    SHOT_DT = 0.01
    SHOT_STEPS = 2000
    # Held fixed across every wind setting, so the chart frame never jumps. Sized
    # to clear the whole slider: an 80 m/s tailwind reaches 412 m, and the highest
    # apex anywhere in the range is 137 m at no wind.
    PLOT_LIMITS = (420.0, 145.0)
    return ANGLES, DRAG, GRAVITY, PLOT_LIMITS, SHOT_DT, SHOT_STEPS, SPEEDS


@app.cell
def _(DRAG, GRAVITY, SHOT_DT, SHOT_STEPS, np):
    def fire(angles_deg, speeds, wind=0.0, record=False):
        """Fire a cannon at every (angle, speed) pair at once.

        Args:
            angles_deg: 1D array of launch angles in degrees, the last axis.
            speeds: 1D array of launch speeds in m/s, the middle axis.
            wind: Horizontal wind in m/s; positive is a tailwind. Drag acts on
                velocity *relative to the air*, which is what lets wind bend the
                whole parameter space instead of just shifting it.
            record: Whether to also return the flight paths. Skipped for the full
                grid, where the arcs would be hundreds of megabytes.

        Returns:
            dict: ``distance`` shaped ``(len(speeds), len(angles))``, plus
                ``path_x``/``path_y`` shaped ``(SHOT_STEPS, *that)`` when
                ``record`` is set (``None`` otherwise). Paths are ``nan`` after
                landing so plotted lines stop at the ground.
        """
        angle = np.deg2rad(np.asarray(angles_deg, dtype=float))[None, :]
        speed = np.asarray(speeds, dtype=float)[:, None]
        shape = np.broadcast(angle, speed).shape

        x = np.zeros(shape)
        y = np.zeros(shape)
        vx = np.broadcast_to(speed * np.cos(angle), shape).copy()
        vy = np.broadcast_to(speed * np.sin(angle), shape).copy()
        flying = np.ones(shape, dtype=bool)
        distance = np.zeros(shape)
        path_x = np.full((SHOT_STEPS, *shape), np.nan) if record else None
        path_y = np.full((SHOT_STEPS, *shape), np.nan) if record else None

        for step in range(SHOT_STEPS):
            if not flying.any():
                break
            airborne = flying.copy()

            relative_vx = vx - wind
            v = np.hypot(relative_vx, vy)
            nvx = vx + SHOT_DT * (-DRAG * v * relative_vx)
            nvy = vy + SHOT_DT * (-GRAVITY - DRAG * v * vy)
            nx = x + SHOT_DT * nvx
            ny = y + SHOT_DT * nvy

            # Interpolate the ground crossing. Without this the range field has a
            # visible staircase from the fixed time step.
            landed = airborne & (ny < 0)
            if landed.any():
                frac = y[landed] / np.maximum(y[landed] - ny[landed], 1e-12)
                distance[landed] = x[landed] + frac * (nx[landed] - x[landed])
                flying &= ~landed

            x = np.where(flying, nx, x)
            y = np.where(flying, ny, y)
            vx = np.where(flying, nvx, vx)
            vy = np.where(flying, nvy, vy)

            if record:
                path_x[step] = np.where(airborne, nx, np.nan)
                path_y[step] = np.where(airborne, ny, np.nan)
                path_x[step][landed] = distance[landed]
                path_y[step][landed] = 0.0

        distance[flying] = x[flying]  # still airborne when the clock ran out
        return {"distance": distance, "path_x": path_x, "path_y": path_y}

    return (fire,)


@app.cell
def _(mo):
    wind = mo.ui.slider(-80.0, 80.0, step=0.5, value=0.0, label="wind (m/s)", show_value=True)
    return (wind,)


@app.cell
def _(ANGLES, COL_COLOR, HeatmapSelect, ROW_COLOR, SPEEDS, fire, mo):
    # Built ONCE, deliberately without referencing `wind`. The cell below mutates
    # this same widget via set_image() rather than constructing a new one — that
    # is what keeps a committed selection alive across a wind change.
    #
    # `cannon_grid` is exposed separately on purpose: marimo re-runs whichever
    # cells reference a UI element when you interact with it, so the wind cell
    # reaches the widget through `cannon_grid` instead of `cannon`. Referencing
    # `cannon` there would re-simulate the entire parameter space on every mouse
    # move. The pendulum below is wired up exactly the same way.
    cannon_grid = HeatmapSelect(
        fire(ANGLES, SPEEDS)["distance"],
        cmap="gray",
        x_range=(ANGLES[0], ANGLES[-1]),
        y_range=(SPEEDS[0], SPEEDS[-1]),
        x_label="launch\nangle",
        y_label="speed",
        x_suffix="°",
        cell_width=4,
        cell_height=4,
        # Same hexes the chart below uses, so a blue band and a blue fan of arcs
        # are obviously the same selection.
        row_color=ROW_COLOR,
        col_color=COL_COLOR,
    )
    # Not displayed here — the chart cell renders it beside the trajectories.
    cannon = mo.ui.anywidget(cannon_grid)
    return cannon, cannon_grid


@app.cell
def _(ANGLES, SPEEDS, cannon_grid, fire, wind):
    # Recompute the parameter space for this wind and push only the bitmap.
    # set_image touches image_base64/n_rows/n_cols and nothing else, so
    # the three pins survive untouched.
    distance = fire(ANGLES, SPEEDS, wind=wind.value)["distance"]
    cannon_grid.set_image(distance)
    return (distance,)


@app.cell
def _(wind):
    wind
    return


@app.cell(hide_code=True)
def _(Hint, cannon, mo, shot_fig):
    # `cannon` is displayed here and nowhere else. Rendering one marimo element in
    # two cells gives you two DOM copies of the same model, and their canvases can
    # drift apart.
    mo.hstack(
        [
            Hint(cannon, "hover/click/explore the axes", side="top"),
            shot_fig,
        ],
        justify="start",
        align="center",
        gap=1,
    )
    return


@app.cell(hide_code=True)
def _(distance, mo):
    # Same live key as the pendulum's below: what the greys mean, in real units,
    # derived from the data so it cannot go stale.
    mo.md(
        f"**range** — dark: the ball barely leaves the barrel · bright: it carries "
        f"the furthest this wind allows. This field runs **0** to "
        f"**{distance.max():.0f} m**."
    )
    return


@app.cell(hide_code=True)
def _(
    ANGLES,
    CELL_COLOR,
    COL_COLOR,
    PLOT_LIMITS,
    ROW_COLOR,
    SPEEDS,
    cannon,
    fire,
    plt,
    wind,
):
    # Abstracting over a parameter means drawing every run at once, the way Victor
    # overlays all the car trajectories for a swept road bend. Because the three
    # pins coexist, all three layers can be on screen together — deciding what
    # that combination should look like is exactly the caller's job.
    shot_fig, shot_ax = plt.subplots(figsize=(3.6, 3.9))
    shot_drew = False


    def shot_fan(angles, speeds, **style):
        shots = fire(angles, speeds, wind=wind.value, record=True)
        xs = shots["path_x"].reshape(shots["path_x"].shape[0], -1)
        ys = shots["path_y"].reshape(shots["path_y"].shape[0], -1)
        shot_ax.plot(xs, ys, **style)


    # Hover layers first, so a pin always draws over its own preview. Each keeps
    # its axis colour and just goes thin and transparent — coarser subsampling
    # too, since these redraw on every mouse move.
    if cannon.hover_row is not None:
        shot_fan(
            ANGLES[::6],
            [SPEEDS[cannon.hover_row]],
            color=ROW_COLOR,
            linewidth=0.7,
            alpha=0.2,
        )
        shot_drew = True

    if cannon.hover_col is not None:
        shot_fan(
            [ANGLES[cannon.hover_col]],
            SPEEDS[::6],
            color=COL_COLOR,
            linewidth=0.7,
            alpha=0.25,
        )
        shot_drew = True

    if cannon.hover_cell is not None:
        shot_hover_row, shot_hover_col = cannon.hover_cell
        shot_fan(
            [ANGLES[shot_hover_col]],
            [SPEEDS[shot_hover_row]],
            color=CELL_COLOR,
            linewidth=1.0,
            alpha=0.35,
        )
        shot_drew = True

    if cannon.pinned_row is not None:
        # Speed held, every angle swept.
        shot_fan(
            ANGLES[::3],
            [SPEEDS[cannon.pinned_row]],
            color=ROW_COLOR,
            linewidth=0.8,
            alpha=0.45,
        )
        shot_drew = True

    if cannon.pinned_col is not None:
        # Angle held, every speed swept.
        shot_fan(
            [ANGLES[cannon.pinned_col]],
            SPEEDS[::3],
            color=COL_COLOR,
            linewidth=0.8,
            alpha=0.55,
        )
        shot_drew = True

    if cannon.pinned_cell is not None:
        # Slicing happens here in Python — the widget only reports indices.
        shot_cell_row, shot_cell_col = cannon.pinned_cell
        shot_fan(
            [ANGLES[shot_cell_col]],
            [SPEEDS[shot_cell_row]],
            color=CELL_COLOR,
            linewidth=1.8,
        )
        shot_drew = True

    if not shot_drew:
        shot_ax.text(0.5, 0.5, "nothing selected", ha="center", va="center", color="#999999")
        shot_ax.set_axis_off()
    else:
        # Fixed limits, so changing the wind swaps the curves without also
        # rescaling the frame underneath them.
        shot_ax.set_xlim(0, PLOT_LIMITS[0])
        shot_ax.set_ylim(0, PLOT_LIMITS[1])
        shot_ax.axhline(0.0, color="#999999", linewidth=1.0)
        shot_ax.set_xlabel("metres downrange")
        shot_ax.set_ylabel("height (m)")
        shot_ax.spines[["top", "right"]].set_visible(False)

    shot_fig.tight_layout()

    # The parameter space and the trajectories it stands for, side by side. The
    # widget is only *displayed* here, not created here, so re-running this cell
    # on hover reuses the same element rather than resetting it.
    return (shot_fig,)


@app.cell(hide_code=True)
def _(ANGLES, cannon, distance, mo):
    # Always three bullets in the same order, pinned or not, and each kept short
    # enough not to wrap. A readout that grows as you click would shove the widget
    # below it down the page mid-gesture, which turns every click into a jump.
    if cannon.pinned_cell is None:
        shot_cell_line = "- **cell** — *nothing pinned*"
    else:
        shot_row, shot_col = cannon.pinned_cell
        shot_cell_line = (
            f"- **cell** — {cannon.x_at(shot_col):.0f}° at "
            f"{cannon.y_at(shot_row):.0f} m/s travels "
            f"**{distance[shot_row, shot_col]:.0f} m**"
        )

    if cannon.pinned_row is None:
        shot_row_line = "- **row** — *nothing pinned*"
    else:
        shot_best = distance[cannon.pinned_row].argmax()
        shot_row_line = (
            f"- **row** — at {cannon.y_at(cannon.pinned_row):.0f} m/s the "
            f"furthest is **{distance[cannon.pinned_row, shot_best]:.0f} m**, at "
            f"**{ANGLES[shot_best]:.0f}°**"
        )

    if cannon.pinned_col is None:
        shot_col_line = "- **column** — *nothing pinned*"
    else:
        shot_col_line = (
            f"- **column** — at {cannon.x_at(cannon.pinned_col):.0f}° the best any "
            f"speed manages is **{distance[:, cannon.pinned_col].max():.0f} m**"
        )

    mo.md("\n".join([shot_cell_line, shot_row_line, shot_col_line]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. A field you can only poke — a double pendulum

    ### The setup

    Two rigid rods, 1 m each, hanging off a fixed pivot: the **upper arm** from the
    pivot, the **lower arm** off the end of the upper one. Equal weights on both
    ends. You hold the two arms out at some pair of angles, both measured from
    *straight down*, and let go.

    So one cell of the grid is one experiment. **The x axis is the angle you hold
    the upper arm at, the y axis is the angle you hold the lower arm at.** 121
    values each, from −170° to +170°, which is 14 641 releases.

    ### Starting spin

    "Let go" is not the only option — you can also give the upper arm a shove on
    the way out. That is what the **starting spin** slider sets: the upper arm's
    angular velocity at the instant you release, in radians per second. **Spin = 0
    means you just let go**, hands off, no push. Positive spins it one way,
    negative the other.

    It earns its own slider because it does something the geometry alone cannot.
    At **spin = 0** the picture comes out perfectly symmetric: holding both arms
    at *minus* their angles is the same experiment seen in a mirror, so it has to
    give the same answer. Any spin at all breaks that, because the mirror image
    reverses a spin but you kept pushing the same way.

    ### What the colours mean

    Every cell gets simulated for a full **8 seconds**, and you can colour the grid
    by any of three readings off that one run — the toggle is below. Switching
    between them re-colours instantly; nothing is re-simulated.

    | Reading | Dark cell | Bright cell |
    | --- | --- | --- |
    | **flip time** | goes over the top almost at once | still swinging after 8 s |
    | **distance travelled** | lower end barely moves | lower end covers ~60 m |
    | **highest point** | lower end never comes up | lower end reaches the very top |

    `flip time` is the only one that can be undefined: about half of these releases
    **never** get an arm over the top, because being held at rest below the pivot
    simply does not buy enough height to pay for it. Those cells have no flip time,
    so they come out as `nan`, and `nan` gets the
    <span style="color:#2f5d47">**green**</span> "bad" colour. The other two
    readings are defined everywhere, so switching to them makes the green vanish.

    Whichever you pick, the edge of that region is fractal: two releases 3° apart
    can behave completely differently, and no amount of staring gives you a rule.
    Pinning things is the only move.

    ### Reading the picture beside the grid

    Nothing is subsampled there — a pinned row is drawn as **all 121** of its
    releases, which is why it reads as a swept region rather than as a few curves.

    | On the chart | Means |
    | --- | --- |
    | solid rods, filled joints | the arms **as you let go**, one per release |
    | thin curve | the path the **lower end** takes, stopping the instant it flips |
    | dashed rods, hollow joints | where a single pinned or hovered release **ends up** |
    | small dot | where one release of a *sweep* ends up — 121 of them per sweep |
    | grey cross | the pivot |

    "Ends up" means at 8 seconds for a release that never flips, and the last pose
    before going over for one that does — the same moment its path stops, so the
    dashed arms always sit at the end of the curve rather than somewhere past it.
    """)
    return


@app.cell
def _(np):
    N = 121  # cells per axis; 121 x 3px is the same footprint as the cannon grid
    # Deliberately not the full +-180: a cell released at exactly 180 is already
    # at the flip threshold, so it would "flip" on the first step and paint the
    # whole border as instant. Wikipedia's version of this picture stops at 3 rad
    # for the same reason.
    THETA_DEG = np.linspace(-170.0, 170.0, N)
    THETA = np.deg2rad(THETA_DEG)

    G = 9.81
    L1 = L2 = 1.0  # rod lengths (m)
    M1 = M2 = 1.0  # bob masses (kg)
    DT = 0.02  # integration step; see simulate_field's docstring
    T_MAX = 8.0  # give up after this and call it "never flips"

    # Rods are rigid, so the lower bob can never leave this box no matter what the
    # spin is. Held fixed so changing the spin never rescales the frame.
    REACH = 2.15
    # The colormap's "bad" color, for the ~45% of cells that never flip. A third
    # hue, deliberately not in the blue/orange family: violet-blue here reads as
    # a stray row band, and it has to say "this is an outcome" rather than "this
    # is background showing through".
    NEVER_COLOR = "#2f5d47"
    return (
        DT,
        G,
        L1,
        L2,
        M1,
        M2,
        N,
        NEVER_COLOR,
        REACH,
        THETA,
        THETA_DEG,
        T_MAX,
    )


@app.cell
def _(G, L1, L2, M1, M2, np):
    def derivatives(state):
        """Time derivatives of ``(theta1, theta2, omega1, omega2)``.

        The textbook two-point-mass double pendulum. Every operation is
        elementwise, so ``state`` can hold one pendulum or fifteen thousand.

        Args:
            state: Tuple of four arrays of matching shape — the two arm angles
                measured from straight down, and their angular velocities.

        Returns:
            tuple: Four arrays of the same shape, ``(omega1, omega2, alpha1,
                alpha2)``.
        """
        theta1, theta2, omega1, omega2 = state
        delta = theta1 - theta2
        denominator = 2 * M1 + M2 - M2 * np.cos(2 * delta)

        alpha1 = (
            -G * (2 * M1 + M2) * np.sin(theta1)
            - M2 * G * np.sin(theta1 - 2 * theta2)
            - 2 * np.sin(delta) * M2 * (omega2 * omega2 * L2 + omega1 * omega1 * L1 * np.cos(delta))
        ) / (L1 * denominator)
        alpha2 = (
            2
            * np.sin(delta)
            * (
                omega1 * omega1 * L1 * (M1 + M2)
                + G * (M1 + M2) * np.cos(theta1)
                + omega2 * omega2 * L2 * M2 * np.cos(delta)
            )
        ) / (L2 * denominator)
        return omega1, omega2, alpha1, alpha2


    def rk4_step(state, dt):
        """Advance a state by ``dt`` with classical Runge-Kutta 4."""
        k1 = derivatives(state)
        k2 = derivatives(tuple(s + 0.5 * dt * k for s, k in zip(state, k1)))
        k3 = derivatives(tuple(s + 0.5 * dt * k for s, k in zip(state, k2)))
        k4 = derivatives(tuple(s + dt * k for s, k in zip(state, k3)))
        return tuple(
            s + dt / 6 * (a + 2 * b + 2 * c + d) for s, a, b, c, d in zip(state, k1, k2, k3, k4)
        )

    return (rk4_step,)


@app.cell
def _(DT, L1, L2, N, THETA, T_MAX, np, rk4_step):
    def simulate_field(spin):
        """Simulate every release for the full ``T_MAX`` and read three things off it.

        Row index is the lower arm's angle, column index is the upper arm's, which
        is what ``origin="lower"`` on the widget expects.

        Two shortcuts here are deliberate, both measured against a reference run at
        ``dt=0.01`` in float64:

        - ``DT`` is 0.02, not 0.01. Halving it agrees on 99.7% of the never-flip
          classifications and moves the median flip time by 0.01s, for twice the
          wall clock. This is a picture, not an ephemeris.
        - float32, worth another ~2x and equally invisible in the result.

        Together they put all three fields at just under half a second, which is
        what makes the spin slider draggable rather than a submit button. An
        earlier version also *dropped* cells from the integration as they flipped,
        which was faster still — but distance and height need the whole 8 seconds,
        and three readings off one honest run beats one reading off a fast one.

        Args:
            spin: Angular velocity given to the upper arm at the moment of
                release, rad/s. Zero means simply let go, which is what makes the
                fields exactly symmetric.

        Returns:
            dict: Three ``(N, N)`` float32 arrays.

                - ``flip``: seconds until either arm first passes straight up, or
                  ``nan`` if neither ever does. ``nan`` is what the widget paints
                  in the colormap's "bad" color.
                - ``travel``: metres covered by the lower end over the 8 seconds.
                - ``highest``: the highest the lower end ever gets, in metres
                  relative to the pivot, so bounded to ``[-2, +2]`` by the rods.
        """
        theta1 = np.repeat(THETA[None, :], N, axis=0).ravel().astype(np.float32)
        theta2 = np.repeat(THETA[:, None], N, axis=1).ravel().astype(np.float32)
        state = (
            theta1,
            theta2,
            np.full(theta1.shape, spin, dtype=np.float32),
            np.zeros_like(theta1),
        )

        def lower_end(angles1, angles2):
            """Where the far end of the lower arm is, pivot at the origin."""
            return (
                L1 * np.sin(angles1) + L2 * np.sin(angles2),
                -L1 * np.cos(angles1) - L2 * np.cos(angles2),
            )

        x, y = lower_end(state[0], state[1])
        flip = np.full(N * N, np.nan, dtype=np.float32)
        travel = np.zeros(N * N, dtype=np.float32)
        highest = y.copy()

        for step in range(int(round(T_MAX / DT))):
            state = rk4_step(state, DT)
            next_x, next_y = lower_end(state[0], state[1])
            travel += np.hypot(next_x - x, next_y - y)
            np.maximum(highest, next_y, out=highest)
            x, y = next_x, next_y
            # Angles are never wrapped, so "past straight up" is just a magnitude
            # test — and only the first crossing is recorded.
            flipped = (np.abs(state[0]) > np.pi) | (np.abs(state[1]) > np.pi)
            flip = np.where(flipped & np.isnan(flip), (step + 1) * DT, flip)

        return {
            "flip": flip.reshape(N, N),
            "travel": travel.reshape(N, N),
            "highest": highest.reshape(N, N),
        }

    return (simulate_field,)


@app.cell
def _(DT, L1, L2, np, rk4_step):
    def swing(theta1, theta2, spin, seconds):
        """Run a set of pendulums and record the path plus the poses at each end.

        No compaction and no float32 here, unlike ``simulate_field``: this draws a
        picture you look at closely, and even all 121 releases of a full sweep is a
        tenth of the work of the grid.

        Args:
            theta1: Upper arm release angle(s) in radians. Broadcast against
                ``theta2``, so one of the two may be a scalar.
            theta2: Lower arm release angle(s) in radians.
            spin: Angular velocity given to the upper arm at release, rad/s.
            seconds: How long to run for.

        Returns:
            dict: Five arrays.

                - ``x``/``y``, ``(steps, n_runs)``: the path of the lower end,
                  ``nan`` from the moment that run flips, so a plotted line simply
                  stops there.
                - ``pose_x``/``pose_y``, ``(3, n_runs)``: pivot, elbow and lower
                  end at t=0 — the arms as you let go of them, ready to plot as a
                  stick figure.
                - ``end_x``/``end_y``, the same three points for where each run
                  *finishes*. For a run that flips that is the last pose before it
                  went over, matching where its path stops rather than carrying on
                  past it; for a run that never flips it is the pose at
                  ``seconds``.
        """
        start1, start2 = np.broadcast_arrays(
            np.atleast_1d(np.asarray(theta1, dtype=float)),
            np.atleast_1d(np.asarray(theta2, dtype=float)),
        )
        start1, start2 = start1.ravel(), start2.ravel()

        state = (
            start1.copy(),
            start2.copy(),
            np.full(start1.shape, float(spin)),
            np.zeros_like(start1),
        )
        steps = int(round(seconds / DT))
        xs = np.full((steps, start1.size), np.nan)
        ys = np.full((steps, start1.size), np.nan)
        swinging = np.ones(start1.size, dtype=bool)
        # The latest angles each run was seen at while still swinging. `swinging`
        # is updated before these, so a run that just went over the top keeps the
        # pose it had on the step before — the one its path stops at.
        final1, final2 = start1.copy(), start2.copy()

        for step in range(steps):
            state = rk4_step(state, DT)
            swinging &= (np.abs(state[0]) <= np.pi) & (np.abs(state[1]) <= np.pi)
            elbow_x, elbow_y = L1 * np.sin(state[0]), -L1 * np.cos(state[0])
            xs[step] = np.where(swinging, elbow_x + L2 * np.sin(state[1]), np.nan)
            ys[step] = np.where(swinging, elbow_y - L2 * np.cos(state[1]), np.nan)
            final1 = np.where(swinging, state[0], final1)
            final2 = np.where(swinging, state[1], final2)

        def stick(angles1, angles2):
            """Pivot, elbow, lower end — three points ready to plot as two rods."""
            elbow_x = L1 * np.sin(angles1)
            elbow_y = -L1 * np.cos(angles1)
            zero = np.zeros_like(angles1)
            return (
                np.stack([zero, elbow_x, elbow_x + L2 * np.sin(angles2)]),
                np.stack([zero, elbow_y, elbow_y - L2 * np.cos(angles2)]),
            )

        pose_x, pose_y = stick(start1, start2)
        end_x, end_y = stick(final1, final2)
        return {
            "x": xs,
            "y": ys,
            "pose_x": pose_x,
            "pose_y": pose_y,
            "end_x": end_x,
            "end_y": end_y,
        }

    return (swing,)


@app.cell
def _(NEVER_COLOR, Normalize, PowerNorm, T_MAX, matplotlib):
    # Everything that differs between the three readings, in one place: which array
    # to colour by, how to scale it, what the units are, and the plain-English
    # gloss the caption under the grid prints. `peak` names what the biggest value
    # in a slice actually is, so the readout can stay generic.
    #
    # Every norm has explicit ends rather than autoscaling. Otherwise dragging the
    # spin slider would rescale the colours too, and the picture would change
    # brightness for a reason that has nothing to do with the physics.
    GRAY_BAD = matplotlib.colormaps["gray"].with_extremes(bad=NEVER_COLOR)

    METRICS = {
        "flip time": {
            "field": "flip",
            "unit": "s",
            "cmap": GRAY_BAD,
            # Half the cells flip between 1s and 3.5s, so a linear ramp over the
            # full eight buries the filaments in a narrow band of grays. The gamma
            # pulls that bulk apart without clipping the long survivors.
            "norm": PowerNorm(0.6, vmin=0.0, vmax=T_MAX),
            "limits": (0.0, T_MAX),
            "dark": "goes over the top almost at once",
            "bright": f"still swinging after {T_MAX:.0f} s",
            "peak": "slowest to flip",
            "note": (
                "About half of these releases never get an arm over the top at "
                "all. Those have no flip time, so they are `nan`, and `nan` is "
                'drawn in the colormap\'s <b>green</b> "bad" colour.'
            ),
        },
        "distance travelled": {
            "field": "travel",
            "unit": "m",
            "cmap": GRAY_BAD,
            "norm": Normalize(vmin=0.0, vmax=70.0),
            "limits": (0.0, 70.0),
            "dark": "the lower end barely moves",
            "bright": "the lower end covers tens of metres",
            "peak": "furthest travelled",
            "note": (
                "Total path length of the lower end over the 8 seconds. Defined "
                "for every release, so nothing is green here."
            ),
        },
        "highest point": {
            "field": "highest",
            "unit": "m",
            "cmap": GRAY_BAD,
            # Bounded by the rods, not by the data: the lower end lives on a circle
            # of radius L1 + L2 about the pivot, so +-2 m is the whole world.
            "norm": Normalize(vmin=-2.0, vmax=2.0),
            "limits": (-2.0, 2.0),
            "dark": "the lower end stays down near the bottom",
            "bright": "the lower end makes it to the very top",
            "peak": "got highest",
            "note": (
                "Height of the highest point the lower end reaches, measured from "
                "the pivot, so mid-gray is level with it. Rod lengths bound this "
                "to -2 m … +2 m whatever the spin is."
            ),
        },
    }
    return (METRICS,)


@app.cell
def _(METRICS, mo):
    spin = mo.ui.slider(
        -3.0,
        3.0,
        step=0.1,
        value=1.2,
        label="starting spin on the upper arm (rad/s) — 0 means just let go",
        show_value=True,
    )
    metric = mo.ui.radio(
        options=list(METRICS),
        value="flip time",
        label="colour the grid by",
        inline=True,
    )
    return metric, spin


@app.cell
def _(COL_COLOR, HeatmapSelect, ROW_COLOR, THETA_DEG, mo, np):
    # Built once and mutated via set_image, same as the cannon above. The starting
    # image is a throwaway of the right shape — the cell below immediately paints
    # the real one, and doing it that way keeps this cell free of any reference to
    # the spin slider or the metric toggle.
    pendulum_grid = HeatmapSelect(
        np.zeros((len(THETA_DEG), len(THETA_DEG))),
        x_range=(THETA_DEG[0], THETA_DEG[-1]),
        y_range=(THETA_DEG[0], THETA_DEG[-1]),
        x_label="upper\nangle",
        y_label="lower\nangle",
        x_suffix="°",
        y_suffix="°",
        cell_width=3,
        cell_height=3,
        row_color=ROW_COLOR,
        col_color=COL_COLOR,
    )
    pendulum = mo.ui.anywidget(pendulum_grid)
    return pendulum, pendulum_grid


@app.cell
def _(simulate_field, spin):
    # The only expensive cell on the page, and the only one the spin slider
    # touches. All three readings come out of this one run.
    fields = simulate_field(spin.value)
    return (fields,)


@app.cell
def _(METRICS, fields, metric, pendulum_grid):
    # Re-colour, don't re-simulate: switching the toggle only reaches this cell, so
    # it is a repaint of numbers that are already in hand. set_image touches
    # image_base64/n_rows/n_cols and nothing else, so the three pins live through
    # both this and a spin change.
    chosen = METRICS[metric.value]
    values = fields[chosen["field"]]
    pendulum_grid.set_image(values, cmap=chosen["cmap"], norm=chosen["norm"])
    return chosen, values


@app.cell
def _(metric, mo, spin):
    mo.vstack([spin, metric])
    return


@app.cell(hide_code=True)
def _(chosen, metric, mo, np, values):
    # The legend the widget itself does not draw. Stating the live min and max in
    # real units is the difference between "some grey squares" and a reading you
    # can trust — and it is derived from the data, so it cannot go stale.
    mo.md(
        f"**{metric.value}** — dark: {chosen['dark']} · "
        f"bright: {chosen['bright']}. This field runs "
        f"**{np.nanmin(values):.2f}** to **{np.nanmax(values):.2f} "
        f"{chosen['unit']}**.<br>{chosen['note']}"
    )
    return


@app.cell(hide_code=True)
def _(
    CELL_COLOR,
    COL_COLOR,
    REACH,
    ROW_COLOR,
    THETA,
    T_MAX,
    mo,
    np,
    pendulum,
    plt,
    spin,
    swing,
):
    swing_fig, swing_ax = plt.subplots(figsize=(3.6, 3.6))
    swing_drew = False


    def polyline(columns):
        """Flatten a ``(points, runs)`` array into one nan-separated line.

        Handing matplotlib a single Line2D instead of 121 of them is about 40%
        faster, and this cell redraws on every mouse move. The appended nan column
        is what stops the end of one run joining up to the start of the next.
        """
        separated = np.hstack([columns.T, np.full((columns.shape[1], 1), np.nan)])
        return separated.ravel()


    def trace(theta1, theta2, color, linewidth, alpha):
        """Draw a whole selection: every release in it, arms and path, no sampling.

        A pinned row *is* all 121 releases along that row. Drawing a handful of
        them and calling it the row was a lie that looked like six unrelated
        curves — the eye had no way to know whether it was seeing the selection or
        an arbitrary subset of it. At full density the overlap builds up as tone
        instead, and a sweep reads as the swept *region* it stands for, which is
        the whole point of abstracting over a parameter.

        There was never a performance reason to sample: 121 runs cost 30ms to draw
        against 17ms for seven, on top of 10ms of simulation. So the alphas are
        low and the strokes are hairlines, and density does the work.
        """
        runs = swing(theta1, theta2, spin.value, T_MAX)
        swing_ax.plot(
            polyline(runs["x"]),
            polyline(runs["y"]),
            color=color,
            linewidth=linewidth,
            alpha=alpha,
        )
        # Dots on the joints help you read one pendulum and turn 121 of them into
        # mush, so they are for a single release only.
        single = runs["x"].shape[1] == 1
        joints = {"marker": "o", "markersize": 4.5} if single else {}
        swing_ax.plot(
            polyline(runs["pose_x"]),
            polyline(runs["pose_y"]),
            color=color,
            linewidth=linewidth * 1.8,
            alpha=min(1.0, alpha * 1.8),
            solid_capstyle="round",
            **joints,
        )
        # Where it ends up. Solid arms are the release, dashed arms are the finish.
        # For a sweep, 121 dashed skeletons stipple the fan into noise and you lose
        # the thing the fan is for, so all a sweep gets is one dot per run at its
        # final lower end. That is the useful aggregate anyway: the spread of those
        # dots is the chaos, and some of them sit above the pivot.
        if single:
            swing_ax.plot(
                polyline(runs["end_x"]),
                polyline(runs["end_y"]),
                color=color,
                linewidth=linewidth * 1.8,
                alpha=min(1.0, alpha * 1.8),
                linestyle=(0, (2.5, 2)),
                marker="o",
                markersize=4.5,
                markerfacecolor="white",
            )
        else:
            swing_ax.plot(
                runs["end_x"][2],
                runs["end_y"][2],
                color=color,
                linestyle="none",
                marker="o",
                markersize=1.8,
                alpha=min(1.0, alpha * 5.0),
            )
        return runs


    # Hover layers first, so a pin always draws over its own preview.
    if pendulum.hover_row is not None:
        trace(THETA, THETA[pendulum.hover_row], ROW_COLOR, 0.4, 0.05)
        swing_drew = True

    if pendulum.hover_col is not None:
        trace(THETA[pendulum.hover_col], THETA, COL_COLOR, 0.4, 0.05)
        swing_drew = True

    if pendulum.hover_cell is not None:
        swing_hover_row, swing_hover_col = pendulum.hover_cell
        trace(
            THETA[swing_hover_col],
            THETA[swing_hover_row],
            CELL_COLOR,
            0.7,
            0.4,
        )
        swing_drew = True

    if pendulum.pinned_row is not None:
        # Lower arm held, every one of the 121 upper angles swept.
        trace(THETA, THETA[pendulum.pinned_row], ROW_COLOR, 0.4, 0.1)
        swing_drew = True

    if pendulum.pinned_col is not None:
        # Upper arm held, every one of the 121 lower angles swept.
        trace(THETA[pendulum.pinned_col], THETA, COL_COLOR, 0.4, 0.1)
        swing_drew = True

    if pendulum.pinned_cell is not None:
        swing_cell_row, swing_cell_col = pendulum.pinned_cell
        trace(
            THETA[swing_cell_col],
            THETA[swing_cell_row],
            CELL_COLOR,
            1.2,
            0.85,
        )
        swing_drew = True

    if not swing_drew:
        swing_ax.text(0.5, 0.5, "nothing selected", ha="center", va="center", color="#999999")
    else:
        # Rods are rigid, so this frame is the whole reachable world and it never
        # needs rescaling. The cross marks the pivot the arms hang from.
        swing_ax.set_xlim(-REACH, REACH)
        swing_ax.set_ylim(-REACH, REACH)
        swing_ax.set_aspect("equal")
        swing_ax.plot([0], [0], marker="+", color="#999999", markersize=9)
    swing_ax.set_axis_off()
    swing_fig.tight_layout()

    mo.hstack([pendulum, swing_fig], justify="start", align="center", gap=1)
    return


@app.cell(hide_code=True)
def _(THETA_DEG, chosen, metric, mo, np, pendulum, values):
    # Same fixed three lines as the cannon's readout, and for the same reason — see
    # the comment there. Reports whichever reading the toggle selected, in that
    # reading's own units, so the words can never contradict the picture.
    def pend_sweep(sliced, swept):
        """One line for a 1D slice: its span, and where the biggest value sits."""
        if np.isnan(sliced).all():
            return f"no {metric.value} anywhere along it"
        biggest = int(np.nanargmax(sliced))
        return (
            f"spans **{np.nanmin(sliced):.2f}–{np.nanmax(sliced):.2f} "
            f"{chosen['unit']}**, {chosen['peak']} at {swept} "
            f"**{THETA_DEG[biggest]:.0f}°**"
        )


    if pendulum.pinned_cell is None:
        pend_cell_line = "- **cell** — *nothing pinned*"
    else:
        pend_row, pend_col = pendulum.pinned_cell
        pend_value = values[pend_row, pend_col]
        pend_cell_line = (
            f"- **cell** — upper {pendulum.x_at(pend_col):.0f}° / lower "
            f"{pendulum.y_at(pend_row):.0f}° → "
            + (
                "**never flips**"
                if np.isnan(pend_value)
                else f"**{pend_value:.2f} {chosen['unit']}**"
            )
        )

    if pendulum.pinned_row is None:
        pend_row_line = "- **row** — *nothing pinned*"
    else:
        pend_row_line = (
            f"- **row** — lower arm at {pendulum.y_at(pendulum.pinned_row):.0f}°: "
            + pend_sweep(values[pendulum.pinned_row], "upper")
        )

    if pendulum.pinned_col is None:
        pend_col_line = "- **column** — *nothing pinned*"
    else:
        pend_col_line = (
            f"- **column** — upper arm at "
            f"{pendulum.x_at(pendulum.pinned_col):.0f}°: "
            + pend_sweep(values[:, pendulum.pinned_col], "lower")
        )

    mo.md("\n".join([pend_cell_line, pend_row_line, pend_col_line]))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### One rung down the ladder

    A pinned row or column is a 1D slice through the field, and because the values
    never left Python, drawing it is `values[widget.pinned_row]` — no second
    simulation. Flattening one dimension out turns the fractal into a comb of
    spikes: neighbours 3° apart survive for wildly different times, and the gaps
    are the stretches that never flip at all. That is what "chaotic" looks like
    when you only get one axis to say it in.
    """)
    return


@app.cell(hide_code=True)
def _(COL_COLOR, ROW_COLOR, THETA_DEG, chosen, metric, pendulum, plt, values):
    slice_fig, slice_ax = plt.subplots(figsize=(7.3, 1.9))
    sliced = False

    if pendulum.hover_row is not None:
        slice_ax.plot(THETA_DEG, values[pendulum.hover_row], color=ROW_COLOR, alpha=0.25)
        sliced = True
    if pendulum.hover_col is not None:
        slice_ax.plot(THETA_DEG, values[:, pendulum.hover_col], color=COL_COLOR, alpha=0.25)
        sliced = True
    if pendulum.pinned_row is not None:
        slice_ax.plot(
            THETA_DEG,
            values[pendulum.pinned_row],
            color=ROW_COLOR,
            label=f"lower arm held at {pendulum.y_at(pendulum.pinned_row):.0f}°",
        )
        sliced = True
    if pendulum.pinned_col is not None:
        slice_ax.plot(
            THETA_DEG,
            values[:, pendulum.pinned_col],
            color=COL_COLOR,
            label=f"upper arm held at {pendulum.x_at(pendulum.pinned_col):.0f}°",
        )
        sliced = True

    if not sliced:
        slice_ax.text(
            0.5,
            0.5,
            "pin or hover a row or column",
            ha="center",
            va="center",
            color="#999999",
        )
        slice_ax.set_axis_off()
    else:
        slice_ax.set_xlim(THETA_DEG[0], THETA_DEG[-1])
        # Fixed to the metric's own ends, so neither the spin slider nor a
        # different slice can rescale the curve out from under you.
        slice_ax.set_ylim(*chosen["limits"])
        slice_ax.set_xlabel("swept angle (°)")
        slice_ax.set_ylabel(f"{metric.value} ({chosen['unit']})")
        slice_ax.spines[["top", "right"]].set_visible(False)
        if slice_ax.get_legend_handles_labels()[1]:
            # Above the frame, not inside it — the spikes reach the top of the
            # axes often enough that any in-frame corner eventually collides.
            slice_ax.legend(
                loc="lower right",
                bbox_to_anchor=(1.0, 1.0),
                ncols=2,
                frameon=False,
                fontsize=8,
            )
    slice_fig.tight_layout()
    slice_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The coloring is just matplotlib

    `HeatmapSelect` takes a picture, one pixel per cell. Hand it a 2D array and
    it colormaps with matplotlib's own conventions — `cmap`, `norm`, `vmin`,
    `vmax` — defaulting to grayscale. Cells that are **masked or non-finite** get
    the colormap's "bad" color, which is all the pendulum's never-flip island ever
    was: plain `nan`, no special case in the widget. The explicit version works
    too — below, cannon shots that fail to clear 120 m are masked out in red.
    """)
    return


@app.cell
def _(ANGLES, HeatmapSelect, PowerNorm, SPEEDS, distance, matplotlib, mo, np):
    mo.ui.anywidget(
        HeatmapSelect(
            np.ma.masked_where(distance < 120.0, distance),
            cmap=matplotlib.colormaps["magma"].with_extremes(bad="#c81e1e"),
            # Autoscaled, unlike the two widgets above: this one is rebuilt from
            # scratch each run rather than fed through set_image, so there is no
            # earlier picture for its brightness to stay consistent with.
            norm=PowerNorm(0.35),
            x_range=(ANGLES[0], ANGLES[-1]),
            y_range=(SPEEDS[0], SPEEDS[-1]),
            x_label="launch\nangle",
            y_label="speed",
            x_suffix="°",
            cell_width=3,
            cell_height=3,
        )
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## What the widget gives you

    The values behind the picture never cross the wire — the widget hands back
    indices plus data coordinates, and the slicing is yours:

    | Trait | Meaning |
    | --- | --- |
    | `pinned_cell` | `(row, col)` of the pinned cell, or `None` |
    | `pinned_row` | row index pinned from the left axis, or `None` |
    | `pinned_col` | column index pinned from the bottom axis, or `None` |
    | `hover_cell` / `hover_row` / `hover_col` | the same three shapes for the cursor; only one is ever set |

    All six are independent. `x_at(col)` and `y_at(row)` turn an index back into
    a data coordinate, and `clear()` drops everything.
    """)
    return


@app.cell
def _(pendulum):
    pendulum.selection
    return


if __name__ == "__main__":
    app.run()
