# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.36",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # StateViewer

    Watch what happens *inside* a Python function. `StateViewer(search_func, view_func)`
    runs `search_func` once, records every line it executes (recursive calls included),
    and calls `view_func` with the function's local variables at each step. The
    parameter names of `view_func` pick which locals it receives.

    Below: backtracking search for the N-Queens problem. The timeline at the bottom
    plots the recursion depth over the whole run, so you can see each dive and
    backtrack. Click or drag it to scrub, or use ← / → and space when the widget has focus.
    """)
    return


@app.cell
def _():
    import marimo as mo

    from wigglystuff import EsmWidget, StateViewer

    return EsmWidget, StateViewer, mo


@app.function
def solve(board, row, n):
    if row == n:
        return True
    for col in range(n):
        if all(c != col and abs(c - col) != row - r for r, c in enumerate(board)):
            board.append(col)
            if solve(board, row + 1, n):
                return True
            board.pop()
    return False


@app.function
def view(board, n, row=None, col=None):
    cell = 44
    size = cell * n
    attacked = {
        (r, c)
        for qr, qc in enumerate(board)
        for r in range(n)
        for c in range(n)
        if c == qc or abs(c - qc) == abs(r - qr)
    }
    # Checkerboard as one SVG pattern instead of n*n rects: every distinct
    # board is stored in the widget, so a small SVG keeps 8x8 runs light.
    parts = [
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<defs><pattern id="board" width="{2 * cell}" height="{2 * cell}" patternUnits="userSpaceOnUse">'
        f'<rect width="{2 * cell}" height="{2 * cell}" fill="#f0d9b5"/>'
        f'<rect x="{cell}" width="{cell}" height="{cell}" fill="#b58863"/>'
        f'<rect y="{cell}" width="{cell}" height="{cell}" fill="#b58863"/>'
        f'</pattern></defs><rect width="{size}" height="{size}" fill="url(#board)"/>'
    ]
    # In the rows that still need a queen, cross out every square a placed
    # queen attacks; the uncrossed squares are the free ones.
    crosses = []
    for r, c in sorted(attacked):
        if r >= len(board):
            x0, y0, x1, y1 = c * cell + 14, r * cell + 14, (c + 1) * cell - 14, (r + 1) * cell - 14
            crosses.append(f"M{x0},{y0}L{x1},{y1}M{x1},{y0}L{x0},{y1}")
    if crosses:
        parts.append(
            f'<path d="{"".join(crosses)}" stroke="#b91c1c" stroke-width="3" '
            f'stroke-linecap="round" opacity="0.75"/>'
        )
    if row is not None and col is not None and row < n and row == len(board):
        ok = (row, col) not in attacked
        parts.append(
            f'<rect x="{col * cell + 2}" y="{row * cell + 2}" width="{cell - 4}" '
            f'height="{cell - 4}" fill="none" stroke="{"#16a34a" if ok else "#dc2626"}" '
            f'stroke-width="4" rx="4"/>'
        )
    for r, c in enumerate(board):
        parts.append(
            f'<text x="{c * cell + cell / 2}" y="{r * cell + cell * 0.72}" '
            f'font-size="{cell * 0.7}" text-anchor="middle" fill="#111">♛</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


@app.cell
def _(mo):
    n = mo.ui.slider(4, 8, value=8, label="board size", show_value=True)
    n
    return (n,)


@app.cell
def _(StateViewer, mo, n):
    viewer = mo.ui.anywidget(StateViewer(solve, view, args=([], 0, n.value), max_steps=20_000))
    viewer
    return (viewer,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    The whole trace is available from Python too. `viewer.steps` holds one record per
    step (line, depth, locals), and `viewer.step` follows the widget whenever you pause
    or scrub.
    """)
    return


@app.cell
def _(viewer):
    viewer.widget.current
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Searches without recursion

    The timeline plots call depth by default, which only says something when the
    function calls itself. A loop-based search keeps its progress in a data structure
    instead, so tell the timeline what to plot with `timeline_func`. Like `view_func`,
    its parameter names pick the locals:

    ```python
    StateViewer(search, maze_view, args=..., timeline_func=lambda frontier: len(frontier))
    ```

    Below, one function does both searches; the only difference is which end of
    `frontier` it pops from. Breadth-first (a queue) keeps a narrow band of cells
    at the same distance and finds the shortest path. Depth-first (a stack) keeps
    pushing deeper, so its frontier piles up, and its path wanders.
    """)
    return


@app.function
def search(maze, start, goal, breadth_first):
    frontier = [start]
    came_from = {start: None}
    while frontier:
        node = frontier.pop(0) if breadth_first else frontier.pop()
        if node == goal:
            break
        r, c = node
        for nxt in [(r - 1, c), (r, c + 1), (r + 1, c), (r, c - 1)]:
            if maze[nxt[0]][nxt[1]] != "#" and nxt not in came_from:
                came_from[nxt] = node
                frontier.append(nxt)
    path = []
    while node is not None:
        path.append(node)
        node = came_from[node]
    return path[::-1]


@app.function
def maze_view(maze, came_from=(), frontier=(), node=None, path=None):
    # Defaults for everything but `maze`: the first steps run before
    # `frontier` and `came_from` exist, and the bare maze should show then too.
    cell = 26
    width, height = cell * len(maze[0]), cell * len(maze)

    def squares(cells, fill):
        # One <path> per colour keeps each stored view small.
        d = "".join(f"M{c * cell},{r * cell}h{cell}v{cell}h-{cell}z" for r, c in cells)
        return f'<path d="{d}" fill="{fill}"/>' if d else ""

    walls = [(r, c) for r, row in enumerate(maze) for c, ch in enumerate(row) if ch == "#"]
    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
        squares(came_from, "#bfdbfe"),
        squares(frontier, "#fb923c"),
        squares(walls, "#334155"),
    ]
    if path:
        points = " ".join(f"{c * cell + cell / 2},{r * cell + cell / 2}" for r, c in path)
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="#16a34a" stroke-width="6" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
    if node is not None:
        r, c = node
        parts.append(
            f'<circle cx="{c * cell + cell / 2}" cy="{r * cell + cell / 2}" r="{cell * 0.32}" fill="#2563eb"/>'
        )
    for r, row in enumerate(maze):
        for c, ch in enumerate(row):
            if ch in "SG":
                parts.append(
                    f'<text x="{c * cell + cell / 2}" y="{r * cell + cell * 0.7}" font-size="15" '
                    f'font-weight="700" text-anchor="middle" fill="#0f172a">{ch}</text>'
                )
    parts.append("</svg>")
    return "".join(parts)


@app.cell
def _(mo):
    MAZE = [
        "#################",
        "#S......#.......#",
        "#.......#.......#",
        "#..######...###.#",
        "#.......#...#...#",
        "#####...#...#.###",
        "#.......#...#...#",
        "#.####..##.##...#",
        "#...........#..G#",
        "#################",
    ]
    strategy = mo.ui.radio(
        options=["breadth-first (queue)", "depth-first (stack)"],
        value="breadth-first (queue)",
        inline=True,
    )
    strategy
    return MAZE, strategy


@app.cell
def _(MAZE, StateViewer, mo, strategy):
    maze_viewer = mo.ui.anywidget(
        StateViewer(
            search,
            maze_view,
            args=(MAZE, (1, 1), (8, 15), strategy.value.startswith("breadth")),
            timeline_func=lambda frontier: len(frontier),
            timeline_label="frontier size",
            variables=["node", "frontier", "path"],
        )
    )
    maze_viewer
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Drive another widget

    `view_func` is optional. The widget's real job is to publish where the run is:
    `step` syncs to Python while you play or scrub, and `viewer.state` holds the actual
    local values at that step. So any other widget can draw the state.

    Below, a StateViewer without a view (and with only a few variables in its table) drives
    a three.js board inside an `EsmWidget`. The cell that wires them only updates the
    widget's `data`; it never recreates the widget, so you can drag to rotate and scroll to
    zoom while the search plays.
    """)
    return


@app.function
def board_data(board, n, row=None, col=None):
    # Plain JSON for the 3D module: where the queens are, which open squares
    # are attacked, and which square the search is trying right now.
    attacked = [
        [r, c]
        for r in range(len(board), n)
        for c in range(n)
        if any(c == qc or abs(c - qc) == abs(r - qr) for qr, qc in enumerate(board))
    ]
    trying = None
    if row is not None and col is not None and row < n and row == len(board):
        trying = [row, col, [row, col] not in attacked]
    return {"n": n, "board": list(board), "attacked": attacked, "trying": trying}


@app.cell(hide_code=True)
def _():
    BOARD_3D = """
        import * as THREE from "https://esm.sh/three@0.170.0";
        import { OrbitControls } from "https://esm.sh/three@0.170.0/examples/jsm/controls/OrbitControls.js";

        const LIGHT = 0xf0d9b5, DARK = 0xb58863, HIT = 0xd97a7a, OK = 0x16a34a, BAD = 0xdc2626;

        export default {
          render({ model, el }) {
            const width = el.clientWidth || 640, height = el.clientHeight || 420;
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(width, height);
            renderer.shadowMap.enabled = true;
            el.appendChild(renderer.domElement);

            const scene = new THREE.Scene();
            scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 1.6));
            const sun = new THREE.DirectionalLight(0xffffff, 1.6);
            sun.position.set(4, 10, 6);
            sun.castShadow = true;
            scene.add(sun);

            const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
        // Stay above the board.
        controls.maxPolarAngle = Math.PI * 0.45;

            // A queen: a lathe-turned body with a ball on top.
            const profile = [[0.34, 0], [0.34, 0.08], [0.2, 0.16], [0.13, 0.5], [0.22, 0.62], [0.12, 0.7], [0, 0.72]];
            const queenBody = new THREE.LatheGeometry(profile.map(([x, y]) => new THREE.Vector2(x, y)), 32);
            const queenTop = new THREE.SphereGeometry(0.08, 16, 12).translate(0, 0.78, 0);
            const queenMaterial = new THREE.MeshStandardMaterial({ color: 0x5b21b6, roughness: 0.35 });

            let n = 0, tiles = [], queens = [], board = null;

            function build(size) {
              if (board) scene.remove(board);
              board = new THREE.Group();
              scene.add(board);
              n = size;
              tiles = [];
              queens = [];
              const tileGeometry = new THREE.BoxGeometry(0.98, 0.12, 0.98);
              for (let r = 0; r < n; r++) {
                for (let c = 0; c < n; c++) {
                  const tile = new THREE.Mesh(tileGeometry, new THREE.MeshStandardMaterial({ roughness: 0.8 }));
                  tile.position.set(c - (n - 1) / 2, -0.06, r - (n - 1) / 2);
                  tile.receiveShadow = true;
                  tile.userData.base = (r + c) % 2 === 0 ? LIGHT : DARK;
                  board.add(tile);
                  tiles.push(tile);
                }
              }
              for (let r = 0; r < n; r++) {
                const queen = new THREE.Group();
                for (const geometry of [queenBody, queenTop]) {
                  const part = new THREE.Mesh(geometry, queenMaterial);
                  part.castShadow = true;
                  queen.add(part);
                }
                queen.visible = false;
                queen.userData.target = new THREE.Vector3();
                board.add(queen);
                queens.push(queen);
              }
              camera.position.set(n * 0.8, n * 1.05, n * 1.15);
              controls.target.set(0, 0, 0);
              controls.update();
            }

            function update() {
              const data = model.get("data") || {};
              if (!data.n) return;
              if (data.n !== n) build(data.n);
              const hit = new Set((data.attacked || []).map(([r, c]) => r * n + c));
              tiles.forEach((tile, i) => tile.material.color.setHex(hit.has(i) ? HIT : tile.userData.base));
              if (data.trying) {
                const [r, c, ok] = data.trying;
                tiles[r * n + c].material.color.setHex(ok ? OK : BAD);
              }
              queens.forEach((queen, r) => {
                if (r >= data.board.length) {
                  queen.visible = false;
                  return;
                }
                queen.userData.target.set(data.board[r] - (n - 1) / 2, 0, r - (n - 1) / 2);
                // A freshly placed queen drops in from above; a moved one glides.
                if (!queen.visible) queen.position.copy(queen.userData.target).setY(0.8);
                queen.visible = true;
              });
            }

            let frame = requestAnimationFrame(function tick() {
              for (const queen of queens) if (queen.visible) queen.position.lerp(queen.userData.target, 0.3);
              controls.update();
              renderer.render(scene, camera);
              frame = requestAnimationFrame(tick);
            });

            update();
            model.on("change:data", update);
            return () => {
              cancelAnimationFrame(frame);
              model.off("change:data", update);
              controls.dispose();
              renderer.dispose();
            };
          },
        };
    """
    return (BOARD_3D,)


@app.cell(expand_output=True)
def _(BOARD_3D, EsmWidget, StateViewer, mo, n):
    viewer3d = mo.ui.anywidget(
        StateViewer(
            solve,
            args=([], 0, n.value),
            variables=["board", "row", "col"],
            max_steps=20_000,
            sync_throttle_ms=50,
        )
    )
    # A plain widget, not mo.ui.anywidget: nothing needs to rerun when it changes.
    board3d = EsmWidget(BOARD_3D, data=board_data([], n.value), width=640, height=420)
    # Show both from this cell: it doesn't rerun on steps, so the 3D view keeps its camera.
    mo.vstack([viewer3d, board3d])
    return board3d, viewer3d


@app.cell
def _(board3d, n, viewer3d):
    # Reruns on every synced step and only swaps the data of the existing widget;
    # the module's change:data handler updates the scene without rebuilding it.
    _state = viewer3d.widget.state or {}
    board3d.data = board_data(
        _state.get("board", []), n.value, _state.get("row"), _state.get("col")
    )
    return


if __name__ == "__main__":
    app.run()
