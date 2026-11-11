# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.39",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    import marimo as mo

    # Prefer the local checkout so this demo tracks the in-repo FormulaDAG even
    # before it lands in a published wigglystuff release.
    repo_root = Path(__file__).resolve().parents[1]
    if (repo_root / "wigglystuff").exists():
        sys.path.insert(0, str(repo_root))

    from wigglystuff import EsmWidget, FormulaDAG

    return EsmWidget, FormulaDAG, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # FormulaDAG

    Write each formula once, and refer to another formula's output with
    `\use{name}`. The widget renders that formula's output symbol in place,
    infers the edge, and lays everything out top to bottom by dependency
    depth. Each arrow lands right above the spot where the output is used.

    Hover a formula to highlight what it depends on and what depends on it.
    """)
    return


@app.cell
def _(FormulaDAG, mo):
    stats = mo.ui.anywidget(
        FormulaDAG(
            {
                "mu": r"\mu = \frac{1}{n}\sum_{i=1}^{n} x_i",
                "var": r"\sigma^2 = \frac{1}{n}\sum_{i=1}^{n} (x_i - \use{mu})^2",
                "sigma": r"\sigma = \sqrt{\use{var}}",
                "z": {
                    "tex": r"z_i = \frac{x_i - \use{mu}}{\note{scale}{\use{sigma}}}",
                    "label": "z-score",
                },
            },
            notes={"scale": "distance measured in standard deviations"},
        )
    )
    stats
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A bigger one: Black–Scholes, with draggable inputs

    Shared pieces (the discount factor, the volatility over the horizon) feed
    several formulas, and `d1` is used both by `d2` and, skipping a row, by the
    call price.

    Each formula also carries an `fn` (e.g. `lambda d1, vol: d1 - vol`), so the
    widget computes every value live. The values fill the legend's second row
    (hover one of those chips to light that output up in the DAG). While you
    drag a number, every formula that depends on it swaps its symbol for the
    live value, both where it's defined and wherever it's used, so you can
    watch the change ripple through. Let go and the symbols come back.

    The market inputs are `\tangle{...}` numbers shared across the whole DAG:
    drag `S`, `K`, `r`, `σ` or `T` sideways in any formula (or click one to type)
    and every formula showing it follows. The legend under the DAG says what each
    one means (its `label`); its chips scrub too, and hovering one lights up every
    place that number appears. `\note{name}{...}` adds the
    plain-language notes. Click a formula to select it.
    """)
    return


@app.cell(expand_output=True)
def _(FormulaDAG, mo):
    from math import erf, exp, log, sqrt

    def N(x):
        return 0.5 * (1 + erf(x / sqrt(2)))

    def _number(value, lo, hi, step, symbol, label, digits=2):
        return {
            "value": value,
            "label": label,
            "min_value": lo,
            "max_value": hi,
            "step": step,
            "digits": digits,
            "display": "symbol",
            "symbol": symbol,
        }

    bs = mo.ui.anywidget(
        FormulaDAG(
            {
                "vol": {
                    "tex": r"\sigma_T = \tangle{sigma}\sqrt{\tangle{T}}",
                    "label": "volatility to expiry",
                    "fn": lambda sigma, T: sigma * sqrt(T),
                },
                "disc": {
                    "tex": r"D = \note{discount}{e^{-\tangle{r}\tangle{T}}}",
                    "label": "discount factor",
                    "fn": lambda r, T: exp(-r * T),
                },
                "d1": {
                    "tex": r"\note{d1}{d_1} = \frac{\note{moneyness}{\ln(\tangle{S}/\tangle{K})} + (\tangle{r} + \tfrac{1}{2}\tangle{sigma}^2)\tangle{T}}{\use{vol}}",
                    "label": "hedge distance",
                    "fn": lambda S, K, r, sigma, T, vol: (log(S / K) + (r + sigma**2 / 2) * T) / vol,
                },
                "d2": {
                    "tex": r"\note{d2}{d_2} = \use{d1} - \use{vol}",
                    "label": "exercise distance",
                    "fn": lambda d1, vol: d1 - vol,
                },
                "call": {
                    "tex": r"C = \tangle{S}\,N(\use{d1}) - \tangle{K}\,\use{disc}\,\note{exercise}{N(\use{d2})}",
                    "label": "call price",
                    "digits": 2,
                    "fn": lambda S, K, d1, d2, disc: S * N(d1) - K * disc * N(d2),
                },
                "put": {
                    "tex": r"P = \use{call} - \tangle{S} + \tangle{K}\,\use{disc}",
                    "label": "put (via parity)",
                    "digits": 2,
                    "fn": lambda call, S, K, disc: call - S + K * disc,
                },
                "delta": {
                    "tex": r"\Delta_C = N(\use{d1})",
                    "label": "call delta",
                    "fn": lambda d1: N(d1),
                },
            },
            parameters={
                "S": _number(100, 50, 150, 1, "S", "spot price", digits=0),
                "K": _number(100, 50, 150, 1, "K", "strike", digits=0),
                "r": _number(0.05, 0, 0.2, 0.005, "r", "risk-free rate", digits=3),
                "sigma": _number(0.2, 0.05, 1, 0.01, r"\sigma", "volatility"),
                "T": _number(1, 0.1, 5, 0.1, "T", "years to expiry", digits=1),
            },
            notes={
                "d1": "distance to the strike in units of $\\sigma_T$; $N(d_1)$ is the hedge ratio",
                "d2": "one $\\sigma_T$ less than $d_1$; $N(d_2)$ is the chance of exercise",
                "discount": "today's value of 1 paid at $T$",
                "moneyness": "how far the stock is above the strike",
                "exercise": "risk-neutral chance the call ends in the money",
            },
        )
    )
    bs
    return (bs,)


@app.cell
def _(bs, mo):
    # Each formula's `fn` runs in Python whenever a number changes; the results
    # land in `outputs`. `committed_outputs` keeps the results from before the
    # drag until you let go, so mid-drag we can show what changed.
    _now, _was = bs.outputs, bs.committed_outputs

    def _show(key, digits):
        text = f"**{key}** {_now[key]:.{digits}f}"
        if bs.dragging and abs(_now[key] - _was[key]) > 10**-digits / 2:
            text += f" _(was {_was[key]:.{digits}f})_"
        return text

    mo.md(" · ".join([_show("call", 2), _show("put", 2), _show("delta", 3)]))
    return


@app.cell
def _(bs, mo):
    _name = bs.selected
    mo.md(
        f"**Selected:** `{_name}` — depends on `{sorted(bs.upstream(_name))}`, "
        f"feeds into `{sorted(bs.downstream(_name))}`"
        if _name
        else "_Click a formula above to select it._"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Matrices

    A matrix is just LaTeX layout: put a `\tangle{...}` in each cell of a
    `pmatrix` and every entry becomes its own draggable number. The values a
    formula computes are scalars, so here the determinant is live, while the
    inverse reuses the entries in its own `pmatrix`. Drag `d` toward `0.5` and
    watch the determinant pass through zero, where the inverse stops existing.
    """)
    return


@app.cell
def _(FormulaDAG, mo):
    def _entry(name, value, label):
        # Show the letter; it turns into its number while you drag it.
        return {
            "value": value,
            "label": label,
            "min_value": -3,
            "max_value": 3,
            "step": 0.1,
            "display": "symbol",
            "symbol": name,
        }

    matrix = mo.ui.anywidget(
        FormulaDAG(
            {
                "A": {
                    "tex": r"A = \begin{pmatrix} \tangle{a} & \tangle{b} \\ \tangle{c} & \tangle{d} \end{pmatrix}",
                    "label": "the matrix",
                },
                "det": {
                    "tex": r"\Delta = \det \use{A} = \tangle{a}\tangle{d} - \tangle{b}\tangle{c}",
                    "label": "determinant",
                    "digits": 2,
                    "fn": lambda a, b, c, d: a * d - b * c,
                },
                "area": {
                    "tex": r"\text{area} = |\use{det}|",
                    "label": "how much A scales area",
                    "digits": 2,
                    "fn": lambda det: abs(det),
                },
                "inv": {
                    "tex": r"A^{-1} = \frac{1}{\use{det}} \begin{pmatrix} \tangle{d} & -\tangle{b} \\ -\tangle{c} & \tangle{a} \end{pmatrix}",
                    "label": "inverse",
                },
            },
            parameters={
                "a": _entry("a", 2, "top left"),
                "b": _entry("b", 1, "top right"),
                "c": _entry("c", 1, "bottom left"),
                "d": _entry("d", 1, "bottom right"),
            },
        )
    )
    matrix
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Projectile motion, with wind

    A ball launched at speed `v` and angle `θ`, while the wind pushes it with a
    steady acceleration `a_w` toward direction `φ` (0° is a tailwind, 90°
    pushes it to the left). The wind is horizontal, so it doesn't change the
    time in the air; it only bends where the ball lands: `X` downrange and
    `Z` sideways.

    This treats the wind as a constant push. Real wind acts through air drag
    on the ball's speed relative to the air, which has no tidy formula for the
    time of flight.

    Drag `θ` and watch the range peak near 45°. Turn `φ` around to see the
    drift swing from side to side.
    """)
    return


@app.cell
def _(FormulaDAG, mo):
    from math import cos, radians, sin

    def _number(value, lo, hi, step, symbol, label, digits=0):
        return {
            "value": value,
            "min_value": lo,
            "max_value": hi,
            "step": step,
            "digits": digits,
            "display": "symbol",
            "symbol": symbol,
            "label": label,
        }

    projectile = mo.ui.anywidget(
        FormulaDAG(
            {
                "vx": {
                    "tex": r"v_x = \tangle{v}\cos(\tangle{theta}^{\circ})",
                    "label": "forward speed",
                    "digits": 2,
                    "fn": lambda v, theta: v * cos(radians(theta)),
                },
                "vy": {
                    "tex": r"v_y = \tangle{v}\sin(\tangle{theta}^{\circ})",
                    "label": "upward speed",
                    "digits": 2,
                    "fn": lambda v, theta: v * sin(radians(theta)),
                },
                "ax": {
                    "tex": r"a_x = \tangle{wind}\cos(\tangle{phi}^{\circ})",
                    "label": "wind, forward",
                    "digits": 2,
                    "fn": lambda wind, phi: wind * cos(radians(phi)),
                },
                "az": {
                    "tex": r"a_z = \tangle{wind}\sin(\tangle{phi}^{\circ})",
                    "label": "wind, sideways",
                    "digits": 2,
                    "fn": lambda wind, phi: wind * sin(radians(phi)),
                },
                "t": {
                    "tex": r"t = \note{updown}{\frac{2\,\use{vy}}{\tangle{g}}}",
                    "label": "time in the air",
                    "digits": 2,
                    "fn": lambda vy, g: 2 * vy / g,
                },
                "H": {
                    "tex": r"H = \frac{\use{vy}^2}{2\tangle{g}}",
                    "label": "peak height",
                    "digits": 1,
                    "fn": lambda vy, g: vy**2 / (2 * g),
                },
                "X": {
                    "tex": r"X = \use{vx}\,\use{t} + \tfrac{1}{2}\,\use{ax}\,\use{t}^2",
                    "label": "downrange",
                    "digits": 1,
                    "fn": lambda vx, t, ax: vx * t + ax * t**2 / 2,
                },
                "Z": {
                    "tex": r"Z = \note{drift}{\tfrac{1}{2}\,\use{az}\,\use{t}^2}",
                    "label": "sideways drift",
                    "digits": 1,
                    "fn": lambda az, t: az * t**2 / 2,
                },
                "D": {
                    "tex": r"D = \sqrt{\use{X}^2 + \use{Z}^2}",
                    "label": "landing distance",
                    "digits": 1,
                    "fn": lambda X, Z: (X**2 + Z**2) ** 0.5,
                },
            },
            parameters={
                "v": _number(20, 1, 50, 1, "v", "launch speed (m/s)"),
                "theta": _number(45, 1, 89, 1, r"\theta", "launch angle (°)"),
                "g": _number(9.8, 1, 25, 0.1, "g", "gravity (m/s²)", digits=1),
                "wind": _number(1.5, 0, 6, 0.1, "a_w", "wind push (m/s²)", digits=1),
                "phi": _number(60, 0, 355, 5, r"\varphi", "wind direction (°)"),
            },
            # Below, so its arrow doesn't meet the one landing on v_y up top.
            notes={
                "updown": {
                    "text": "up to the peak and back down: twice the rise time",
                    "side": "bottom",
                },
                "drift": "only the wind pushes sideways",
            },
        )
    )
    projectile
    return (projectile,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The throw in 3D, drawn with three.js inside an `EsmWidget` (loaded from a
    CDN, so this view needs internet). Drag to orbit, scroll to zoom. The ground
    legs share the DAG's colors: `X` downrange, then `Z` sideways; the dashed
    orange line is the peak height `H`. The numbers live in the DAG. While you
    drag a number, the throw from before the drag stays as a dashed ghost.
    """)
    return


@app.cell
def _(EsmWidget):
    # three.js from jsDelivr's +esm build; OrbitControls' own `import "three"`
    # is rewritten to the same URL, so both share one copy of three.js.
    _code = r"""
    import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.170.0/+esm";
    import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js/+esm";

    // Nearest .dark/.light marker up the tree (crossing shadow roots), else the OS.
    function isDark(el) {
      for (let n = el; n; n = n.parentNode || n.host) {
        if (n.nodeType !== 1) continue;
        const theme = n.getAttribute("data-theme");
        if (n.classList.contains("dark") || theme === "dark") return true;
        if (n.classList.contains("light") || theme === "light") return false;
      }
      return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
    }

    // The FormulaDAG colors of t, v_y, X and Z, plus neutrals.
    const COLORS = {
      light: { arc: "#147a68", rise: "#b45b1b", x: "#8a6d00", z: "#2f7d32", ink: "#25221d", muted: "#8a8378", grid: "#e4dfd6", ground: "#f6f3ee" },
      dark: { arc: "#5ed5bd", rise: "#ffad66", x: "#e3c35a", z: "#86d38a", ink: "#f2eee8", muted: "#9d968b", grid: "#3a3631", ground: "#1f1d1a" },
    };

    // A round size that fits x: 1, 2, 2.5 or 5 times a power of ten.
    function niceCeil(x) {
      const pow = 10 ** Math.floor(Math.log10(x));
      return [1, 2, 2.5, 5, 10].map((m) => m * pow).find((s) => s >= x);
    }

    const fmt = (x) => (Math.abs(x) >= 100 ? x.toFixed(0) : x.toFixed(1));
    const UNITS = 10; // the throw's size in scene units, whatever its size in meters

    // Physics: x downrange, y up, z sideways (positive = left of the thrower,
    // which is three.js's -z when looking down +x).
    function flight(s) {
      if (!s) return null;
      const T = (2 * s.vy) / s.g;
      return { ...s, T, X: s.vx * T + (s.ax * T * T) / 2, Z: (s.az * T * T) / 2, top: (s.vy * s.vy) / (2 * s.g) };
    }
    const at = (f, t) =>
      new THREE.Vector3(f.vx * t + (f.ax * t * t) / 2, Math.max(0, f.vy * t - (f.g * t * t) / 2), -(f.az * t * t) / 2);
    const pathPoints = (f, n = 120) => Array.from({ length: n + 1 }, (_, i) => at(f, (f.T * i) / n));

    export default {
      render({ model, el }) {
        const W = model.get("width");
        const H = model.get("height");
        const wrap = document.createElement("div");
        wrap.className = "throw3d";
        wrap.style.width = `${W}px`;
        wrap.style.height = `${H}px`;
        const labels = document.createElement("div");
        labels.className = "throw3d__labels";
        const scaleNote = document.createElement("div");
        scaleNote.className = "throw3d__scale";
        el.appendChild(wrap);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(W, H);
        wrap.append(renderer.domElement, labels, scaleNote);

        const scene = new THREE.Scene();
        scene.add(new THREE.HemisphereLight(0xffffff, 0x888888, 2.2));
        const sun = new THREE.DirectionalLight(0xffffff, 1.2);
        sun.position.set(-4, 10, 6);
        scene.add(sun);

        // From the thrower's right side and above: downrange runs left to
        // right across the screen, sideways drift runs into the depth.
        const camera = new THREE.PerspectiveCamera(36, W / H, 0.1, 500);
        camera.position.set(3.5, 7, 13);
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(5, -0.2, -1.5);
        controls.maxPolarAngle = Math.PI / 2 - 0.03; // stay above the ground
        controls.update();

        // The ground stays put in scene units; one square is `meters / UNITS` m.
        const ground = new THREE.Mesh(
          new THREE.PlaneGeometry(22, 22),
          new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.6 }),
        );
        ground.rotation.x = -Math.PI / 2;
        ground.position.set(5, -0.005, 0);
        const grid = new THREE.GridHelper(22, 22);
        grid.position.set(5, 0, 0);
        scene.add(ground, grid);

        // Everything in meters lives in `world`, scaled so the throw spans UNITS.
        const world = new THREE.Group();
        scene.add(world);

        let now = null;
        let was = null;
        let meters = 1; // tweened toward `target`
        let target = 1;
        let colors = COLORS.light;
        let raf = 0;
        const tags = {}; // label name -> {node, at: Vector3 in meters}

        function dispose(group) {
          group.traverse((obj) => {
            obj.geometry?.dispose();
            obj.material?.dispose();
          });
          group.clear();
        }

        function tube(points, radius, color) {
          const curve = new THREE.CatmullRomCurve3(points);
          return new THREE.Mesh(
            new THREE.TubeGeometry(curve, Math.max(8, points.length * 2), radius, 10, false),
            new THREE.MeshStandardMaterial({ color, roughness: 0.55 }),
          );
        }

        function dashed(points, color, opacity = 1) {
          const line = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(points),
            new THREE.LineDashedMaterial({ color, dashSize: target / 60, gapSize: target / 80, transparent: true, opacity }),
          );
          line.computeLineDistances();
          return line;
        }

        function tag(name, text, color, point, place = "below") {
          if (!tags[name]) {
            const node = document.createElement("div");
            node.className = `throw3d__tag throw3d__tag--${place}`;
            labels.appendChild(node);
            tags[name] = { node };
          }
          tags[name].node.textContent = text;
          tags[name].node.style.color = color;
          tags[name].at = point;
        }

        // Rebuild the throw's meshes (cheap: a handful of tubes and lines).
        function build() {
          dispose(world);
          colors = COLORS[isDark(el) ? "dark" : "light"];
          ground.material.color.set(colors.ground);
          wrap.style.setProperty("--halo", colors.ground); // label glow
          grid.material.color.set(colors.grid);
          grid.material.vertexColors = false;
          if (!now) return;
          const r = target / 260; // tube radius: a constant on-screen thickness
          world.add(tube(pathPoints(now), r * 1.4, colors.arc));
          if (was) world.add(dashed(pathPoints(was), colors.muted, 0.9));
          // Its shadow on the ground, to read the sideways drift.
          world.add(dashed(pathPoints(now).map((p) => new THREE.Vector3(p.x, 0.001, p.z)), colors.arc, 0.45));
          // Ground legs: X downrange, then Z sideways. Their numbers are in the
          // DAG above, so the scene only labels the wind.
          const o = new THREE.Vector3(0, 0, 0);
          const corner = new THREE.Vector3(now.X, 0, 0);
          const land = new THREE.Vector3(now.X, 0, -now.Z);
          world.add(tube([o, corner], r, colors.x));
          if (Math.abs(now.Z) > 1e-6) world.add(tube([corner, land], r, colors.z));
          // Peak height, straight down from the top of the arc.
          const peak = at(now, now.T / 2);
          world.add(dashed([new THREE.Vector3(peak.x, 0, peak.z), peak], colors.rise));
          // Landing ring.
          const ring = new THREE.Mesh(
            new THREE.RingGeometry(r * 3, r * 4.5, 32),
            new THREE.MeshBasicMaterial({ color: colors.ink, side: THREE.DoubleSide }),
          );
          ring.rotation.x = -Math.PI / 2;
          ring.position.copy(land).setY(0.002);
          world.add(ring);
          // Wind: a solid arrow behind the thrower, longer when it pushes harder.
          const wind = Math.hypot(now.ax, now.az);
          if (wind > 1e-6) {
            const dir = new THREE.Vector3(now.ax, 0, -now.az).normalize();
            const len = target * (0.05 + 0.025 * wind);
            const head = Math.min(len * 0.4, target * 0.05);
            const center = new THREE.Vector3(-target * 0.14, r * 3, 0);
            const tail = center.clone().addScaledVector(dir, -len / 2);
            const neck = center.clone().addScaledVector(dir, len / 2 - head);
            world.add(tube([tail, neck], r * 1.6, colors.muted));
            const cone = new THREE.Mesh(
              new THREE.ConeGeometry(r * 5, head, 16),
              new THREE.MeshStandardMaterial({ color: colors.muted, roughness: 0.55 }),
            );
            cone.position.copy(neck).addScaledVector(dir, head / 2);
            cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
            world.add(cone);
            tag("wind", `wind ${fmt(wind)} m/s²`, colors.muted, tail, "below");
          } else if (tags.wind) {
            tags.wind.at = null;
          }
        }

        function draw() {
          world.scale.setScalar(UNITS / meters);
          renderer.render(scene, camera);
          // HTML labels follow their 3D points.
          for (const { node, at: point } of Object.values(tags)) {
            if (!point) {
              node.style.display = "none";
              continue;
            }
            const p = world.localToWorld(point.clone()).project(camera);
            node.style.display = p.z < 1 ? "" : "none";
            node.style.left = `${((p.x + 1) / 2) * W}px`;
            node.style.top = `${((1 - p.y) / 2) * H}px`;
          }
          scaleNote.textContent = `1 square = ${fmt(meters / UNITS)} m`;
        }

        // Glide the scale toward the new throw, then stop.
        function frame() {
          meters += (target - meters) * 0.2;
          if (Math.abs(target - meters) < target * 1e-3) meters = target;
          draw();
          raf = meters === target ? 0 : requestAnimationFrame(frame);
        }

        function setData() {
          const data = model.get("data") || {};
          now = flight(data.now);
          was = flight(data.was);
          const fit = [now, was].filter(Boolean).map((f) => Math.max(Math.abs(f.X), Math.abs(f.Z) * 1.4, f.top * 1.6, 1));
          target = fit.length ? niceCeil(Math.max(...fit)) : 1;
          build();
        }

        setData();
        meters = target;
        draw();
        const onData = () => {
          setData();
          if (!raf) raf = requestAnimationFrame(frame);
        };
        model.on("change:data", onData);
        controls.addEventListener("change", draw);
        return () => {
          cancelAnimationFrame(raf);
          model.off("change:data", onData);
          controls.dispose();
          dispose(world);
          renderer.dispose();
        };
      },
    };
    """

    _css = """
    .throw3d { position: relative; border-radius: 10px; overflow: hidden; cursor: grab; }
    .throw3d:active { cursor: grabbing; }
    .throw3d__labels { position: absolute; inset: 0; pointer-events: none; }
    /* A halo in the ground's color, like map labels: it lifts the text and
       knocks out any line passing behind it. */
    .throw3d__tag { position: absolute; white-space: nowrap;
                    font: 600 11px ui-monospace, SFMono-Regular, Menlo, monospace;
                    text-shadow: 0 0 2px var(--halo), 0 0 3px var(--halo), 0 0 5px var(--halo),
                                 0 0 8px var(--halo), 0 0 12px var(--halo); }
    .throw3d__tag--below { transform: translate(-50%, 10px); }
    .throw3d__scale { position: absolute; right: 10px; bottom: 8px; color: #8a8378;
                      font: 10.5px ui-monospace, SFMono-Regular, Menlo, monospace; }
    """

    throw = EsmWidget(_code, css=_css, width=720, height=360)
    throw
    return (throw,)


@app.cell
def _(projectile, throw):
    # Each drag step re-runs this cell; only `data` changes, so the scene
    # rescales smoothly instead of re-rendering. The pre-drag throw is the ghost.
    def _state(outputs, values):
        keys = ("vx", "vy", "ax", "az")
        return {**{k: outputs[k] for k in keys}, "g": values["g"]}

    _now = _state(projectile.outputs, projectile.values)
    _was = _state(projectile.committed_outputs, projectile.committed_values)
    throw.data = {"now": _now, "was": _was if projectile.dragging and _was != _now else None}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Static artifacts

    When the DAG belongs in a doc, blog post or attachment rather than a
    notebook, `to_html()` returns it as a self-contained page — the widget's
    own JS and CSS inlined, KaTeX from the same CDN — and `save()` writes it
    to disk. The page renders the DAG statically: no dragging, editing,
    hovering or selecting.
    """)
    return


@app.cell
def _(bs, mo):
    # to_html() snapshots the current state — drag the Black–Scholes numbers
    # above first and the exported page shows those values and outputs.
    page = bs.widget.to_html(title="Black–Scholes")
    mo.download(page.encode("utf-8"), "black_scholes_dag.html")
    mo.md(f"Exported {len(page):,} bytes of self-contained HTML.")
    return


if __name__ == "__main__":
    app.run()
