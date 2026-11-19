# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "anywidget",
#     "numpy",
#     "wigglystuff==0.6.0",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import sys
    from pathlib import Path

    # Prefer the local checkout so the demo works before the next release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    import marimo as mo
    import numpy as np
    from wigglystuff import (
        CircularSlider,
        FloatingPanel,
        PairPlot,
        TangleSelect,
        ThreeWidget,
        WidgetFlow,
        shape_display,
    )

    return (
        CircularSlider,
        FloatingPanel,
        PairPlot,
        TangleSelect,
        ThreeWidget,
        WidgetFlow,
        mo,
        np,
        shape_display,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A pair plot of a sphere in four dimensions

    You can't look at a sphere in four dimensions, but you can look at its
    shadows. A pair plot does exactly that: every cell drops all coordinates
    but two and shows what is left, so every cell is the sphere's shadow on
    one plane.

    The points are made in two steps. First draw an $n \times d$ matrix
    $\mathbf{G}$ of standard gaussian numbers. A gaussian looks the same in
    every direction, so each row points somewhere uniformly at random. Then
    divide each row by its length $\lVert\mathbf{G}\rVert$: every row of
    $\mathbf{X}$ now has length one, which is to say it lies on the unit
    sphere, spread evenly over it. The thickness slider shakes the length a
    little so the sphere gets a fuzzy shell.

    Every shadow is a disk, but how the points fill it depends on $d$. In
    three dimensions they pile up at the rim, in four they fill the disk
    evenly, and in five they crowd the middle. The histograms on the diagonal
    tell the same story: one coordinate of a point on the sphere has density
    proportional to $(1 - x^2)^{(d-3)/2}$, flat for $d = 3$, a semicircle for
    $d = 4$, a parabola for $d = 5$. The more dimensions, the more of the
    sphere sits near the "equator" of any one axis.
    """)
    return


@app.cell(expand_output=True)
def _(
    CircularSlider,
    PairPlot,
    TangleSelect,
    ThreeWidget,
    WidgetFlow,
    mo,
    np,
    shape_display,
):
    # Everything on screen is made here, once. marimo never reruns the cell
    # that defines a UI element when that element changes, so the flow is
    # drawn a single time and its widgets keep their state. The cells below
    # compute the arrays and push them into the pair plot with `set_data`.
    dims = mo.ui.radio(
        {"3D": 3, "4D": 4, "5D": 5}, value="4D", inline=True, label="dimensions"
    )
    n_points = mo.ui.slider(
        100, 20_000, step=100, value=3_000, show_value=True, full_width=True,
        label="points per sphere",
    )
    inner = mo.ui.switch(value=False, label="inner sphere, radius √½")
    thickness = mo.ui.slider(
        0, 0.3, step=0.01, value=0.0, show_value=True, full_width=True,
        label="thickness",
    )
    new_planes = mo.ui.button(
        label="new random planes", value=0, on_click=lambda count: count + 1
    )
    angle = mo.ui.anywidget(
        CircularSlider(value=0, start=0, stop=360, step=1, size=90, label="θ (degrees)")
    )
    # Controls that feed the same step share one node. A fixed width, so a
    # slider's number growing (100 -> 20,000) can't resize the node and nudge
    # the arrows.
    data_controls = mo.vstack([dims, n_points, inner], gap=0.75).style(width="260px")
    shell_controls = mo.vstack([thickness]).style(width="200px")
    rotation_controls = mo.vstack([angle, new_planes], align="center", gap=0.5)

    # A placeholder row until the cells below send the real data.
    plot = PairPlot(
        np.zeros((1, 4)),
        columns=["y1", "y2", "y3", "y4"],
        cell_size=114,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )
    # Fixed limits, so the camera and the grid never move when the data does.
    three = ThreeWidget(
        data=[],
        width=420,
        height=420,
        xlim=(-1.2, 1.2),
        ylim=(-1.2, 1.2),
        zlim=(-1.2, 1.2),
        show_grid=True,
        axis_labels=["y1", "y2", "y3"],
    )

    # Which columns of Y the 3D view shows. A TangleSelect rather than a
    # marimo dropdown because its `choices` can change on the live widget:
    # the cell below swaps them when d does, without rebuilding the flow.
    def axis_picker(default):
        picker = TangleSelect(choices=["y1", "y2", "y3", "y4"])
        picker.choice = default
        return mo.ui.anywidget(picker)

    axis_x, axis_y, axis_z = axis_picker("y1"), axis_picker("y2"), axis_picker("y3")
    three_panel = mo.vstack(
        [
            mo.hstack(
                [mo.md("axes"), axis_x, axis_y, axis_z],
                justify="start",
                align="center",
                gap=0.5,
            ),
            three,
        ],
        gap=0.5,
    )

    # Mirror the pair plot's selection in the 3D view: selected rows keep
    # their sphere's colour (stored on each point as "base"), the rest fade
    # to grey, like they do in the pair plot itself. An observer on the
    # widget, rather than a marimo cell, so a selection only recolours the
    # 3D points and nothing else reruns.
    def paint_selection(change=None):
        if len(three.data) != len(plot.get_mask()):
            return  # the two are mid-update after a new Y; the next one lands
        if not plot.selection:
            look = [{"color": p["base"], "opacity": 1.0} for p in three.data]
        else:
            look = [
                {"color": p["base"], "opacity": 1.0}
                if picked
                else {"color": "#c4c3bc", "opacity": 0.25}
                for p, picked in zip(three.data, plot.get_mask().tolist())
            ]
        three.update_points(look)

    plot.observe(paint_selection, names="selection")

    # The flow can't depend on `dims` (that would rebuild it, and reset the
    # sliders, on every toggle), so it shows the shapes symbolically. The live
    # sizes are in the row under the flow.
    G_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{G}$")
    r_shape = shape_display(
        np.empty((0, 1)), labels=("n", None), name=r"$\lVert\mathbf{G}\rVert$"
    )
    X_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{X}$")
    Y_shape = shape_display(np.empty((0, 4)), labels=("n", "d"), name=r"$\mathbf{Y}$")

    flow = WidgetFlow(
        [data_controls, G_shape, r_shape, shell_controls, X_shape, rotation_controls, Y_shape, plot, three_panel],
        edges=[
            (data_controls, G_shape, "n, d"),
            (G_shape, r_shape, {"label": "row lengths", "exit": "left", "enter": "right"}),
            (G_shape, X_shape),
            (r_shape, X_shape, "divide"),
            (shell_controls, X_shape),
            (X_shape, Y_shape),
            (rotation_controls, Y_shape, "rotate"),
            (Y_shape, plot),
            (Y_shape, three_panel, "3 picked columns"),
        ],
        labels=[
            (data_controls, "sample"),
            (G_shape, "G"),
            (r_shape, "lengths"),
            (shell_controls, "shell"),
            (X_shape, "X"),
            (rotation_controls, "rotation"),
            (Y_shape, "Y"),
            (plot, "pair plot of Y"),
            (three_panel, "the picked columns in 3D"),
        ],
        notes=[
            (G_shape, "gaussian: the same in every direction"),
            (X_shape, "every row has length 1 (√½ on the inner sphere)"),
        ],
        beside=[
            (r_shape, G_shape, "before"),
            (shell_controls, X_shape, "before"),
            (rotation_controls, Y_shape),
            (three_panel, plot),
        ],
        align="left",
        collapsible=[plot, three_panel],
        # the tab on each dashed frame folds that stretch into one pill
        groups=[
            ("put the points on a sphere", [G_shape, r_shape, shell_controls, X_shape]),
            ("rotate", [rotation_controls, Y_shape]),
        ],
    )
    flow
    return (
        angle,
        axis_x,
        axis_y,
        axis_z,
        dims,
        inner,
        n_points,
        new_planes,
        paint_selection,
        plot,
        thickness,
        three,
    )


@app.cell
def _():
    SPHERE_COLORS = {"outer": "#1f77b4", "inner": "#ff7f0e"}
    return (SPHERE_COLORS,)


@app.cell
def _(dims, inner, n_points, np, shape_display):
    # Fixed seeds, so moving the slider adds points instead of reshuffling.
    # The inner sphere gets its own draw: as many rows, in directions of its own.
    _size = (n_points.value, dims.value)
    _rows = [np.random.default_rng(0).normal(size=_size)]
    if inner.value:
        _rows.append(np.random.default_rng(2).normal(size=_size))
    G = shape_display(np.vstack(_rows), name=r"$\mathbf{G}$")
    # Which sphere each row lands on, and its radius: x1² + ... + xd² = 1 on
    # the outer sphere and 1/2 on the inner one.
    sphere = np.repeat(["outer", "inner"][: len(_rows)], n_points.value)
    radius = np.where(sphere == "inner", 0.5**0.5, 1.0)[:, None]
    return G, radius, sphere


@app.cell
def _(G, np):
    r = np.linalg.norm(G, axis=1, keepdims=True).set_name(r"$\lVert\mathbf{G}\rVert$")
    return (r,)


@app.cell
def _(G, np, r, radius, thickness):
    # Its own fixed seed: the slider scales the same jitter instead of redrawing it.
    _eps = np.random.default_rng(1).normal(size=r.shape)
    X = (G / r * radius * (1 + thickness.value * _eps)).set_name(r"$\mathbf{X}$")
    return (X,)


@app.cell
def _(np):
    def random_basis(d, seed):
        """A uniformly random orthonormal basis of d-dimensional space.

        QR of a gaussian matrix gives an orthogonal Q; matching its signs to
        R's diagonal makes it uniformly random.
        """
        q, r = np.linalg.qr(np.random.default_rng(seed).normal(size=(d, d)))
        return q * np.sign(np.diag(r))

    def rotation_at(basis, theta):
        """Turn by ``theta`` radians in the planes spanned by the basis'
        columns 1-2, 3-4, ...: one plane in 3D (the third axis stays put),
        two in 4D, two in 5D (and the fifth axis stays put)."""
        c, s = np.cos(theta), np.sin(theta)
        turn = np.eye(len(basis))
        for k in range(0, len(basis) - 1, 2):
            turn[k : k + 2, k : k + 2] = [[c, -s], [s, c]]
        return basis @ turn @ basis.T

    return random_basis, rotation_at


@app.cell
def _(dims, new_planes, random_basis):
    # Each click is a new seed, so a new set of planes to turn in.
    basis = random_basis(dims.value, new_planes.value)
    return (basis,)


@app.cell
def _(X, angle, basis, np, rotation_at):
    R = rotation_at(basis, np.radians(angle.value["value"]))
    Y = (X @ R).set_name(r"$\mathbf{Y}$")
    return (Y,)


@app.cell
def _(SPHERE_COLORS, Y, plot, sphere):
    # Update the plot in place: the points move, nothing gets re-created.
    # The cells shrink as d grows so the plot keeps one size: d cells plus
    # the 6px gaps between them come to 474px for d = 3, 4 and 5.
    # hold_sync sends the new size and the new data in one message.
    with plot.hold_sync():
        plot.cell_size = 480 // Y.shape[1] - 6
        plot.set_data(
            Y.value,
            columns=[f"y{i + 1}" for i in range(Y.shape[1])],
            color=sphere,
            color_map=SPHERE_COLORS,
        )
    return


@app.cell
def _(axis_x, axis_y, axis_z, dims):
    # Offer y1 ... yd. A pick that no longer exists (y5 after going back to
    # 4D) falls back to that picker's default.
    _names = [f"y{i + 1}" for i in range(dims.value)]
    for _picker, _default in zip([axis_x, axis_y, axis_z], ["y1", "y2", "y3"]):
        if _picker.widget.choice not in _names:
            _picker.widget.choice = _default
        _picker.widget.choices = _names
    return


@app.cell
def _(
    SPHERE_COLORS,
    Y,
    axis_x,
    axis_y,
    axis_z,
    paint_selection,
    sphere,
    three,
):
    # The same fallback as above, in case this cell runs first after d changes.
    _names = [f"y{i + 1}" for i in range(Y.shape[1])]
    _picked = [
        p.value["choice"] if p.value["choice"] in _names else default
        for p, default in zip([axis_x, axis_y, axis_z], ["y1", "y2", "y3"])
    ]
    _columns = Y.value[:, [_names.index(name) for name in _picked]]
    with three.hold_sync():
        three.axis_labels = _picked
        three.data = [
            {"x": x, "y": y, "z": z, "size": 0.03, "color": c, "base": c, "opacity": 1.0}
            for (x, y, z), c in zip(
                _columns.tolist(), [SPHERE_COLORS[s] for s in sphere]
            )
        ]
    # New axes for the same rows: keep showing the pair plot's selection.
    paint_selection()
    return


@app.cell
def _(G, X, Y, mo, r):
    mo.vstack(
        [
            mo.md("The same arrays, at their live sizes:"),
            mo.hstack([G, r, X, Y], justify="start", gap=3),
        ]
    )
    return


@app.cell(hide_code=True)
def _(dims, mo):
    _look = {
        3: r"""
        **3D.** One coordinate is *uniform* on $[-1, 1]$: the exponent
        $(d-3)/2$ is zero, so the diagonal histograms are flat. This is
        Archimedes' hat-box theorem: slice a sphere into bands of equal
        height and each has the same area. The shadows pile up at the rim,
        where the sphere's surface is seen edge-on.
        """,
        4: r"""
        **4D.** One coordinate has density $\propto (1 - x^2)^{1/2}$, a
        semicircle. Any two coordinates are spread *uniformly* over the disk:
        every off-diagonal cell is an evenly filled circle, with no rim and no
        crowd in the middle.
        """,
        5: r"""
        **5D.** One coordinate has density $\propto 1 - x^2$, a parabola. The
        shadows crowd the centre: with more dimensions to share the unit
        length between, any two coordinates tend to be small together.
        """,
    }
    mo.md(_look[dims.value])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Every three columns at once

    The 3D view above shows the three columns you pick. Here every three
    columns get a cube of their own, next to a pair plot of the same
    $\mathbf{Y}$. With $d = 4$ that is four cubes, one for each column you
    can leave out; with $d = 5$ it is ten. **Drag any cube to turn them all**,
    and double-click to reset. A box you draw in this pair plot, or a range
    across one of its histograms, lights up the same rows in every cube.

    The cubes follow the same rule as the pair plot, one dimension up: $k$ of
    the $d$ coordinates of a point on the sphere have density
    $\propto (1 - r^2)^{(d-k-2)/2}$. So in 4D every cube is a ball whose
    points pile up near its surface, like the disks in 3D, and in 5D every
    cube is an evenly filled ball, like the disks in 4D.
    """)
    return


@app.cell(hide_code=True)
def _(np):
    import itertools

    import anywidget
    import traitlets

    # Every three-column shadow of the data as a small 3D scatter. It is
    # defined right here because it is too specific to this notebook to live
    # in wigglystuff. Plain WebGL (no CDN imports), so it works offline.
    # One WebGL canvas draws every cube in its own viewport; a 2D canvas
    # behind it draws the panels and the back edges of each cube, and one in
    # front draws the front edges and the axis names.
    _TRIPLE_PLOT_JS = r"""
    const GAP = 14;
    const CAPTION = 18;
    const SCALE = 0.54; // keeps the cube's long diagonal (2√3) inside its square
    const DEFAULT_YAW = 35;
    const DEFAULT_PITCH = 20;
    const FONT = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

    // A fixed pseudo-random number per row, so the drawn sample never changes.
    function rowHash(row) {
      let h = Math.imul(row ^ 0x9e3779b9, 0x85ebca6b);
      h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
      return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
    }

    // marimo renders widgets in a shadow root, so walk up through the shadow
    // hosts to find the notebook theme.
    function resolveDark(el) {
      for (let n = el; n; n = n.parentNode || n.host) {
        if (n.nodeType !== 1) continue;
        const cls = n.classList;
        const mode = n.getAttribute("data-theme") || n.getAttribute("data-color-mode");
        if (cls.contains("dark") || cls.contains("dark-theme") || mode === "dark") return true;
        if (cls.contains("light") || cls.contains("light-theme") || mode === "light") return false;
      }
      return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
    }

    function parseColor(color) {
      const probe = document.createElement("canvas").getContext("2d");
      probe.fillStyle = "#000000";
      probe.fillStyle = color;
      const value = probe.fillStyle;
      if (value.startsWith("#")) return [1, 3, 5].map((i) => parseInt(value.slice(i, i + 2), 16) / 255);
      const numbers = (value.match(/[\d.]+/g) || [0, 0, 0]).map(Number);
      return [numbers[0] / 255, numbers[1] / 255, numbers[2] / 255];
    }

    function clamp(value, low, high) {
      return Math.max(low, Math.min(high, value));
    }

    // The camera as three rows: screen right, screen up, and depth (into the
    // screen). Yaw turns around the cube's vertical axis; a positive pitch
    // looks down on it from above.
    function cameraRows(yawDegrees, pitchDegrees) {
      const yaw = (yawDegrees * Math.PI) / 180;
      const pitch = (pitchDegrees * Math.PI) / 180;
      const [cy, sy, cp, sp] = [Math.cos(yaw), Math.sin(yaw), Math.cos(pitch), Math.sin(pitch)];
      return { right: [cy, -sy, 0], up: [sp * sy, sp * cy, cp], depth: [cp * sy, cp * cy, -sp] };
    }

    function dot(row, p) {
      return row[0] * p[0] + row[1] * p[1] + row[2] * p[2];
    }

    // Each point: normalise its three values to [-1, 1], turn them with the
    // camera and drop the depth (an orthographic view). Points further back
    // are fainter, which helps the cloud read as 3D. pointState is 0 for a
    // hidden row, 1 for a normal one and 2 for a selected one; wantState
    // picks which of them a pass draws (0 means every visible row).
    const VERTEX = `
      precision highp float;
      attribute float xValue;
      attribute float yValue;
      attribute float zValue;
      attribute vec3 pointColor;
      attribute float pointState;
      uniform vec2 xDomain;
      uniform vec2 yDomain;
      uniform vec2 zDomain;
      uniform vec3 right;
      uniform vec3 up;
      uniform vec3 depth;
      uniform float scale;
      uniform float pointSize;
      uniform float wantState;
      uniform float useContext;
      uniform vec3 contextColor;
      varying vec3 color;
      varying float fade;
      void main() {
        vec3 p = vec3(
          (xValue - xDomain.x) / (xDomain.y - xDomain.x),
          (yValue - yDomain.x) / (yDomain.y - yDomain.x),
          (zValue - zDomain.x) / (zDomain.y - zDomain.x)
        ) * 2.0 - 1.0;
        bool skip = pointState < 0.5 || (wantState > 0.5 && abs(pointState - wantState) > 0.5);
        gl_Position = skip ? vec4(2.0, 2.0, 0.0, 1.0) : vec4(vec2(dot(right, p), dot(up, p)) * scale, 0.0, 1.0);
        gl_PointSize = pointSize;
        color = mix(pointColor, contextColor, useContext);
        fade = 1.0 - 0.55 * (dot(depth, p) / 1.7320508 * 0.5 + 0.5);
      }
    `;
    const FRAGMENT = `
      precision mediump float;
      uniform float opacity;
      varying vec3 color;
      varying float fade;
      void main() {
        float edge = length(gl_PointCoord - vec2(0.5));
        if (edge > 0.5) discard;
        gl_FragColor = vec4(color, opacity * fade * smoothstep(0.5, 0.36, edge));
      }
    `;

    function makeProgram(gl) {
      const program = gl.createProgram();
      for (const [type, source] of [[gl.VERTEX_SHADER, VERTEX], [gl.FRAGMENT_SHADER, FRAGMENT]]) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
        gl.attachShader(program, shader);
      }
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
      return program;
    }

    // The 8 corners of the cube, and the 12 edges between corners that
    // differ in exactly one coordinate.
    const CORNERS = [];
    for (const x of [-1, 1]) for (const y of [-1, 1]) for (const z of [-1, 1]) CORNERS.push([x, y, z]);
    const EDGES = [];
    for (let i = 0; i < 8; i += 1) {
      for (let j = i + 1; j < 8; j += 1) {
        if ([0, 1, 2].filter((k) => CORNERS[i][k] !== CORNERS[j][k]).length === 1) EDGES.push([i, j]);
      }
    }

    function render({ model, el }) {
      el.classList.add("triple-plot-root");
      el.innerHTML = `
        <div class="tp-status"></div>
        <div class="tp-stage">
          <canvas class="tp-back"></canvas>
          <canvas class="tp-gl"></canvas>
          <canvas class="tp-front"></canvas>
        </div>`;
      const statusEl = el.querySelector(".tp-status");
      const stage = el.querySelector(".tp-stage");
      const [backCanvas, glCanvas, frontCanvas] = stage.querySelectorAll("canvas");
      const back = backCanvas.getContext("2d");
      const front = frontCanvas.getContext("2d");
      const gl = glCanvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
      if (!gl) {
        statusEl.textContent = "This browser has no WebGL.";
        return;
      }
      const program = makeProgram(gl);
      const attribute = (name) => gl.getAttribLocation(program, name);
      const uniform = (name) => gl.getUniformLocation(program, name);
      const loc = {
        x: attribute("xValue"), y: attribute("yValue"), z: attribute("zValue"),
        color: attribute("pointColor"), state: attribute("pointState"),
        domains: [uniform("xDomain"), uniform("yDomain"), uniform("zDomain")],
        right: uniform("right"), up: uniform("up"), depth: uniform("depth"), scale: uniform("scale"),
        pointSize: uniform("pointSize"), opacity: uniform("opacity"), wantState: uniform("wantState"),
        useContext: uniform("useContext"), contextColor: uniform("contextColor"),
      };
      const buffers = { values: gl.createBuffer(), colors: gl.createBuffer(), states: gl.createBuffer() };

      const state = {
        rows: 0,
        columns: 0,
        extents: null, // [low, high] per column
        picked: null, // the row behind every drawn point
        rowState: null, // uint8 per row from Python, or null for "all normal"
        selecting: false,
        selectedCount: 0,
        yaw: model.get("yaw"),
        pitch: model.get("pitch"),
        drag: null,
      };

      // ---- layout: cubes in a near-square grid that fills `width` ----------

      function geometry() {
        const n = model.get("triples").length;
        const width = model.get("width");
        const perRow = Math.max(1, Math.ceil(Math.sqrt(n)));
        const size = Math.floor((width - GAP * (perRow - 1)) / perRow);
        const rows = Math.ceil(n / perRow);
        return { n, size, perRow, width, height: rows * (size + CAPTION) + (rows - 1) * GAP };
      }

      function cubeBox(g, index) {
        const column = index % g.perRow;
        const row = Math.floor(index / g.perRow);
        return { x: column * (g.size + GAP), y: row * (g.size + CAPTION + GAP), size: g.size };
      }

      function resize() {
        const g = geometry();
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        stage.style.width = `${g.width}px`;
        stage.style.height = `${g.height}px`;
        for (const canvas of [backCanvas, glCanvas, frontCanvas]) {
          canvas.style.width = `${g.width}px`;
          canvas.style.height = `${g.height}px`;
          canvas.width = Math.round(g.width * ratio);
          canvas.height = Math.round(g.height * ratio);
        }
        back.setTransform(ratio, 0, 0, ratio, 0, 0);
        front.setTransform(ratio, 0, 0, ratio, 0, 0);
      }

      function theme() {
        const dark = resolveDark(el);
        el.classList.toggle("triple-plot--dark", dark);
        const style = getComputedStyle(el);
        const read = (name) => style.getPropertyValue(name).trim();
        return { ink: read("--tp-ink"), muted: read("--tp-muted"), hair: read("--tp-hair"), panel: read("--tp-panel"), context: read("--tp-context") };
      }

      // ---- WebGL points -----------------------------------------------------

      // Big, solid dots for a few hundred points, small translucent ones when
      // a cube is crowded, so overlap reads as density.
      function pointStyle(count, size) {
        const area = size * size * 0.45; // about how much of the square the cloud covers
        const diameter = clamp(Math.sqrt(area / Math.max(1, count)) * 0.8, 1.5, 5);
        const disc = Math.PI * (diameter / 2) ** 2;
        return { diameter, opacity: clamp((1.8 * area) / (Math.max(1, count) * disc), 0.08, 0.9) };
      }

      function drawPoints(t, g) {
        gl.disable(gl.SCISSOR_TEST);
        gl.viewport(0, 0, glCanvas.width, glCanvas.height);
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
        if (!state.picked || !state.picked.length) return;
        const ratio = glCanvas.width / g.width;
        const count = state.picked.length;
        const base = pointStyle(count, g.size);
        const chosen = pointStyle(Math.max(1, Math.min(count, state.selectedCount)), g.size);
        const camera = cameraRows(state.yaw, state.pitch);

        gl.useProgram(program);
        gl.enable(gl.BLEND);
        gl.blendFuncSeparate(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA, gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
        gl.enable(gl.SCISSOR_TEST);
        gl.uniform3fv(loc.right, camera.right);
        gl.uniform3fv(loc.up, camera.up);
        gl.uniform3fv(loc.depth, camera.depth);
        gl.uniform1f(loc.scale, SCALE);
        gl.uniform3fv(loc.contextColor, parseColor(t.context));
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.colors);
        gl.enableVertexAttribArray(loc.color);
        gl.vertexAttribPointer(loc.color, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.states);
        gl.enableVertexAttribArray(loc.state);
        gl.vertexAttribPointer(loc.state, 1, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.values);

        const pass = (wantState, useContext, style, opacity) => {
          gl.uniform1f(loc.wantState, wantState);
          gl.uniform1f(loc.useContext, useContext);
          gl.uniform1f(loc.pointSize, style.diameter * ratio);
          gl.uniform1f(loc.opacity, opacity);
          gl.drawArrays(gl.POINTS, 0, count);
        };
        model.get("triples").forEach((triple, index) => {
          // Mid-update the triples can run ahead of the data (or lag behind it).
          if (triple.some((column) => column >= state.columns)) return;
          const box = cubeBox(g, index);
          const x = Math.round(box.x * ratio);
          const y = Math.round((g.height - box.y - box.size) * ratio);
          const size = Math.round(box.size * ratio);
          gl.viewport(x, y, size, size);
          gl.scissor(x, y, size, size);
          [loc.x, loc.y, loc.z].forEach((location, k) => {
            gl.enableVertexAttribArray(location);
            gl.vertexAttribPointer(location, 1, gl.FLOAT, false, state.columns * 4, triple[k] * 4);
            gl.uniform2fv(loc.domains[k], state.extents[triple[k]]);
          });
          if (!state.selecting) {
            pass(0, 0, base, base.opacity);
          } else {
            // Grey context first, then the selected rows on top in colour.
            pass(1, 1, base, Math.min(0.5, base.opacity));
            pass(2, 0, chosen, chosen.opacity);
          }
        });
      }

      // ---- 2D: panels, cube edges, axis names, captions ---------------------

      function drawFrames(t, g) {
        back.clearRect(0, 0, g.width, g.height);
        front.clearRect(0, 0, g.width, g.height);
        const camera = cameraRows(state.yaw, state.pitch);
        const names = model.get("columns");
        model.get("triples").forEach((triple, index) => {
          const box = cubeBox(g, index);
          const half = box.size / 2;
          const corners = CORNERS.map((p) => ({
            x: box.x + half + dot(camera.right, p) * SCALE * half,
            y: box.y + half - dot(camera.up, p) * SCALE * half,
            depth: dot(camera.depth, p),
          }));

          back.fillStyle = t.panel;
          back.fillRect(box.x, box.y, box.size, box.size);
          // Edges behind the cloud go on the back canvas, the rest in front.
          for (const [i, j] of EDGES) {
            const ctx = corners[i].depth + corners[j].depth > 0 ? back : front;
            ctx.strokeStyle = t.hair;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(corners[i].x, corners[i].y);
            ctx.lineTo(corners[j].x, corners[j].y);
            ctx.stroke();
          }

          // Each axis is named at the middle of one of its four edges: the one
          // furthest from the centre (so on the outline, never over the
          // points), preferring lower and further left.
          front.font = `11px ${FONT}`;
          front.fillStyle = t.muted;
          front.textAlign = "center";
          front.textBaseline = "middle";
          for (let axis = 0; axis < 3; axis += 1) {
            let best = null;
            for (const [i, j] of EDGES) {
              if (CORNERS[i][axis] === CORNERS[j][axis]) continue;
              const dx = (corners[i].x + corners[j].x) / 2 - (box.x + half);
              const dy = (corners[i].y + corners[j].y) / 2 - (box.y + half);
              const score = Math.hypot(dx, dy) + 0.05 * dy - 0.05 * dx;
              if (!best || score > best.score) best = { dx, dy, score };
            }
            const length = Math.hypot(best.dx, best.dy) || 1;
            const x = clamp(box.x + half + best.dx + (best.dx / length) * 12, box.x + 14, box.x + box.size - 14);
            const y = clamp(box.y + half + best.dy + (best.dy / length) * 12, box.y + 8, box.y + box.size - 8);
            front.fillText(names[triple[axis]] ?? "", x, y);
          }

          front.fillStyle = t.ink;
          front.textBaseline = "top";
          front.fillText(triple.map((column) => names[column] ?? "").join(" · "), box.x + half, box.y + box.size + 4);
        });
      }

      function drawStatus() {
        const cubes = model.get("triples").length;
        const selected = state.selecting ? `${state.selectedCount.toLocaleString()} selected · ` : "";
        statusEl.textContent = `${cubes} ${cubes === 1 ? "cube" : "cubes"} · ${selected}drag to turn them all, double-click to reset`;
      }

      // At most one redraw per frame, however many changes come in.
      let frame = 0;
      function redraw() {
        if (frame) return;
        frame = requestAnimationFrame(() => {
          frame = 0;
          const t = theme();
          const g = geometry();
          drawFrames(t, g);
          drawPoints(t, g);
          drawStatus();
        });
      }

      // ---- data from Python -------------------------------------------------

      function copy(view, Type) {
        return new Type(view.buffer.slice(view.byteOffset, view.byteOffset + view.byteLength));
      }

      function uploadStates() {
        const values = new Float32Array(state.picked.length).fill(1);
        state.selectedCount = 0;
        if (state.rowState) {
          state.picked.forEach((row, i) => (values[i] = state.rowState[row]));
          for (const value of state.rowState) state.selectedCount += value === 2;
        }
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.states);
        gl.bufferData(gl.ARRAY_BUFFER, values, gl.STATIC_DRAW);
      }

      function loadData(message, [matrixView, codeView]) {
        const matrix = copy(matrixView, Float32Array);
        const codes = copy(codeView, Uint8Array);
        const { rows, columns } = message;

        // Axis ranges: the fixed `limits` if given, else the data's, padded.
        const limits = model.get("limits");
        const extents = [];
        for (let column = 0; column < columns; column += 1) {
          if (limits.length === 2) {
            extents.push(limits);
            continue;
          }
          let [low, high] = [Infinity, -Infinity];
          for (let row = 0; row < rows; row += 1) {
            const value = matrix[row * columns + column];
            if (value < low) low = value;
            if (value > high) high = value;
          }
          const pad = high > low ? (high - low) * 0.02 : 1;
          extents.push(Number.isFinite(low) ? [low - pad, high + pad] : [-1, 1]);
        }

        // Every cube draws the same sample, so the total stays under max_marks.
        const perCube = Math.max(100, Math.floor(model.get("max_marks") / Math.max(1, model.get("triples").length)));
        const keep = rows <= perCube ? 1 : perCube / rows;
        const picked = [];
        for (let row = 0; row < rows; row += 1) if (keep === 1 || rowHash(row) < keep) picked.push(row);
        const values = new Float32Array(picked.length * columns);
        const colors = new Float32Array(picked.length * 3);
        const palette = model.get("palette").map(parseColor);
        picked.forEach((row, i) => {
          values.set(matrix.subarray(row * columns, (row + 1) * columns), i * columns);
          colors.set(palette[codes[row]] || [0.16, 0.47, 0.84], i * 3);
        });
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.values);
        gl.bufferData(gl.ARRAY_BUFFER, values, gl.STATIC_DRAW);
        gl.bindBuffer(gl.ARRAY_BUFFER, buffers.colors);
        gl.bufferData(gl.ARRAY_BUFFER, colors, gl.STATIC_DRAW);

        Object.assign(state, { rows, columns, extents, picked, rowState: null, selecting: false });
        uploadStates();
        resize();
        redraw();
      }

      function handleMessage(message, views) {
        if (message.type === "triple-plot-data") {
          loadData(message, views);
        } else if (message.type === "triple-plot-state" && state.picked) {
          state.rowState = copy(views[0], Uint8Array);
          state.selecting = Boolean(message.selecting);
          uploadStates();
          redraw();
        }
      }

      // ---- turning the cubes ------------------------------------------------

      function inCube(event) {
        const rect = frontCanvas.getBoundingClientRect();
        const [x, y] = [event.clientX - rect.left, event.clientY - rect.top];
        const g = geometry();
        for (let index = 0; index < g.n; index += 1) {
          const box = cubeBox(g, index);
          if (x >= box.x && x <= box.x + box.size && y >= box.y && y <= box.y + box.size) return true;
        }
        return false;
      }

      function saveCamera() {
        model.set("yaw", state.yaw);
        model.set("pitch", state.pitch);
        model.save_changes();
      }

      frontCanvas.addEventListener("pointerdown", (event) => {
        if (event.button !== 0 || !inCube(event)) return;
        frontCanvas.setPointerCapture(event.pointerId);
        state.drag = { x: event.clientX, y: event.clientY, yaw: state.yaw, pitch: state.pitch };
        frontCanvas.classList.add("tp-dragging");
      });
      frontCanvas.addEventListener("pointermove", (event) => {
        frontCanvas.classList.toggle("tp-over-cube", state.drag !== null || inCube(event));
        if (!state.drag) return;
        state.yaw = state.drag.yaw - (event.clientX - state.drag.x) * 0.5;
        state.pitch = clamp(state.drag.pitch + (event.clientY - state.drag.y) * 0.5, -89, 89);
        redraw();
      });
      const endDrag = () => {
        if (!state.drag) return;
        state.drag = null;
        frontCanvas.classList.remove("tp-dragging");
        saveCamera();
      };
      frontCanvas.addEventListener("pointerup", endDrag);
      frontCanvas.addEventListener("pointercancel", endDrag);
      frontCanvas.addEventListener("dblclick", (event) => {
        if (!inCube(event)) return;
        state.yaw = DEFAULT_YAW;
        state.pitch = DEFAULT_PITCH;
        redraw();
        saveCamera();
      });

      // ---- listeners --------------------------------------------------------

      const handleCamera = () => {
        if (state.drag) return;
        state.yaw = model.get("yaw");
        state.pitch = model.get("pitch");
        redraw();
      };
      const handleLayout = () => {
        resize();
        redraw();
      };
      model.on("msg:custom", handleMessage);
      model.on("change:yaw change:pitch", handleCamera);
      model.on("change:width change:triples change:columns", handleLayout);
      const media = matchMedia("(prefers-color-scheme: dark)");
      media.addEventListener("change", redraw);
      const themeObserver = new MutationObserver(redraw);
      requestAnimationFrame(() => {
        for (let n = el.parentNode || el.host; n; n = n.parentNode || n.host) {
          if (n.nodeType === 1) themeObserver.observe(n, { attributes: true, attributeFilter: ["class", "data-theme"] });
        }
      });

      resize();
      redraw();
      model.send({ type: "ready" });

      return () => {
        model.off("msg:custom", handleMessage);
        model.off("change:yaw change:pitch", handleCamera);
        model.off("change:width change:triples change:columns", handleLayout);
        media.removeEventListener("change", redraw);
        themeObserver.disconnect();
        cancelAnimationFrame(frame);
        Object.values(buffers).forEach((buffer) => gl.deleteBuffer(buffer));
      };
    }

    export default { render };
    """

    _TRIPLE_PLOT_CSS = """
    .triple-plot-root {
      --tp-ink: #0b0b0b;
      --tp-muted: #85847e;
      --tp-hair: rgba(11, 11, 11, 0.22);
      --tp-panel: #f4f4f2;
      --tp-context: #c4c3bc;
      color-scheme: light dark;
      display: flex;
      flex-direction: column;
      gap: 8px;
      color: var(--tp-ink);
      font: 12px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .triple-plot-root.triple-plot--dark {
      --tp-ink: #f0efec;
      --tp-muted: #8f8e86;
      --tp-hair: rgba(240, 239, 236, 0.24);
      --tp-panel: #232322;
      --tp-context: #4f4e4a;
    }
    .tp-status { color: var(--tp-muted); font-variant-numeric: tabular-nums; }
    .tp-stage { position: relative; }
    .tp-stage canvas { position: absolute; inset: 0; display: block; }
    .tp-front { touch-action: none; }
    .tp-front.tp-over-cube { cursor: grab; }
    .tp-front.tp-dragging { cursor: grabbing; }
    """

    class TriplePlot(anywidget.AnyWidget):
        """One rotatable 3D scatter per three columns of ``X``, all turned
        together. With columns y1..y4 that is (y2, y3, y4), (y1, y3, y4),
        (y1, y2, y4) and (y1, y2, y3). ``follow(pair_plot)`` lights up that
        PairPlot's selection in every cube."""

        _esm = _TRIPLE_PLOT_JS
        _css = _TRIPLE_PLOT_CSS

        columns = traitlets.List(traitlets.Unicode()).tag(sync=True)
        triples = traitlets.List(traitlets.List(traitlets.Int())).tag(sync=True)
        palette = traitlets.List(traitlets.Unicode()).tag(sync=True)
        limits = traitlets.List(traitlets.Float()).tag(sync=True)  # [] or [low, high]
        width = traitlets.Int(480).tag(sync=True)
        max_marks = traitlets.Int(200_000).tag(sync=True)
        yaw = traitlets.Float(35.0).tag(sync=True)
        pitch = traitlets.Float(20.0).tag(sync=True)

        def __init__(self, X, *, columns, width=480, limits=None):
            super().__init__(width=width, limits=list(limits or []))
            self._followed = None
            self.on_msg(self._on_frontend)
            self.set_data(X, columns=columns)

        def set_data(self, X, *, columns, color=None, color_map=None):
            """Show new rows. ``color`` holds one category per row and
            ``color_map`` maps each category to a CSS colour."""
            self._matrix = np.ascontiguousarray(X, dtype=np.float32)
            if color is None:
                self._codes = np.zeros(len(self._matrix), dtype=np.uint8)
                palette = ["#2a78d6"]
            else:
                categories, codes = np.unique(np.asarray(color), return_inverse=True)
                self._codes = codes.astype(np.uint8)
                palette = [color_map[c] for c in categories.tolist()]
            self._state = None
            self._selecting = False
            # Leave out the first column first: (y2, y3, y4) ... (y1, y2, y3).
            d = self._matrix.shape[1]
            with self.hold_sync():
                self.columns = list(columns)
                self.palette = palette
                self.triples = [list(t) for t in reversed(list(itertools.combinations(range(d), 3)))]
            self._send_data()

        def highlight(self, mask=None, *, hidden=None):
            """Colour the rows in ``mask`` and grey out the rest (``None``
            colours every row). Rows where ``hidden`` is true are not drawn."""
            state = np.ones(len(self._matrix), dtype=np.uint8)
            if mask is not None:
                state[np.asarray(mask, dtype=bool)] = 2
            if hidden is not None:
                state[np.asarray(hidden, dtype=bool)] = 0
            self._state = state
            self._selecting = mask is not None
            self._send_state()

        def follow(self, pair_plot):
            """Mirror a PairPlot's selection and filters. Python only hears
            about a selection on release, so the cubes update then too."""
            self._followed = pair_plot
            pair_plot.observe(self._mirror, names=["selection", "filters"])
            self._mirror()

        def _mirror(self, change=None):
            plot = self._followed
            if plot.shape[0] != len(self._matrix):
                return  # mid-update after new data; the next change lands
            mask = plot.get_mask() if plot.selection else None
            hidden = ~plot.get_active_mask() if plot.filters else None
            self.highlight(mask, hidden=hidden)

        def _on_frontend(self, _widget, content, _buffers):
            if content.get("type") == "ready":
                self._send_data()
                self._send_state()

        def _send_data(self):
            rows, columns = self._matrix.shape
            self.send(
                {"type": "triple-plot-data", "rows": int(rows), "columns": int(columns)},
                buffers=[memoryview(self._matrix).cast("B"), memoryview(self._codes)],
            )

        def _send_state(self):
            if self._state is not None:
                self.send(
                    {"type": "triple-plot-state", "selecting": self._selecting},
                    buffers=[memoryview(self._state)],
                )

    return (TriplePlot,)


@app.cell
def _(PairPlot, TriplePlot, mo, np):
    # Made once, like the flow above, and updated in place by the cell below,
    # so the cubes keep their angle when the data changes. Fixed limits, so
    # they don't rescale while the rotation dial turns.
    pairs = PairPlot(
        np.zeros((1, 4)),
        columns=["y1", "y2", "y3", "y4"],
        cell_size=114,
        show_filters=False,
        show_layout_toggle=False,
        show_mode_toggle=False,
    )
    cubes = TriplePlot(
        np.zeros((1, 4)), columns=["y1", "y2", "y3", "y4"], width=480, limits=(-1.2, 1.2)
    )
    cubes.follow(pairs)
    mo.hstack([pairs, cubes], justify="start", align="start", gap=3)
    return cubes, pairs


@app.cell
def _(FloatingPanel, dims, inner, mo, n_points):
    # The sample controls from the flow, pinned so they stay in reach down
    # here. marimo keeps every copy of a UI element in sync, so this panel and
    # the flow drive the same values.
    FloatingPanel(
        mo.vstack([dims, n_points, inner], gap=0.75).style(width="260px"),
        corner="top-right",
        title="sample",
    )
    return


@app.cell
def _(SPHERE_COLORS, Y, cubes, pairs, sphere):
    _columns = [f"y{i + 1}" for i in range(Y.shape[1])]
    # The cubes first: the pair plot's new data clears its selection, and the
    # cubes only follow that once they hold the same rows.
    cubes.set_data(Y.value, columns=_columns, color=sphere, color_map=SPHERE_COLORS)
    with pairs.hold_sync():
        pairs.cell_size = 480 // Y.shape[1] - 6
        pairs.set_data(Y.value, columns=_columns, color=sphere, color_map=SPHERE_COLORS)
    return


if __name__ == "__main__":
    app.run()
