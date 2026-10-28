# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "altair",
#     "marimo",
#     "scipy",
#     "wigglystuff==0.5.36",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup:
    import functools
    import math
    import random
    import sys
    import timeit

    import altair as alt
    import marimo as mo
    from scipy.spatial import ConvexHull

    from wigglystuff import ScatterWidget, StateViewer

    # The drawing area, in drawdata pixels. Views draw it at 0.7x.
    WIDTH, HEIGHT = 600, 400
    # Every point adds steps to every viewer; past this the views get sluggish.
    MAX_POINTS = 60


@app.cell(hide_code=True)
def _():
    mo.md("""
    # Wrapping a convex hull

    Stretch a rubber band around a set of points and let go: the shape it snaps
    to is the *convex hull*. Draw some points below, then watch three classic
    algorithms find it:

    - **Monotone chain**: sweep left to right, keep only left turns.
    - **Gift wrapping**: walk around the outside, one hull point at a time.
    - **Quickhull**: split off the farthest point, recurse on what's outside.

    Press play, or drag a timeline to scrub.
    """)
    return


@app.function
def seed_points(n, seed):
    # drawdata stores pixels with y pointing up, and wants a colour per point.
    rng = random.Random(seed)
    return [
        {"x": rng.uniform(100, 500), "y": rng.uniform(70, 330), "color": "#1f77b4", "label": "a", "batch": 0}
        for _ in range(n)
    ]


@app.cell
def _():
    draw = mo.ui.anywidget(
        ScatterWidget(n_classes=1, width=WIDTH, height=HEIGHT, brushsize=20, data=seed_points(15, 3))
    )
    draw
    return (draw,)


@app.cell
def _(draw):
    # Whole pixels keep the variable tables short and the turn tests exact. The
    # brush can drop two points on the same pixel; the hull needs each only once.
    drawn = sorted({(round(d["x"]), round(d["y"])) for d in draw.data})
    if len(drawn) > MAX_POINTS:
        drawn = sorted(random.Random(0).sample(drawn, MAX_POINTS))
    mo.stop(len(drawn) < 3, mo.md("*Draw at least three points.*"))
    mo.md(f"Hulling **{len(drawn)}** points" + (f" (a sample of {MAX_POINTS})." if len(draw.data) > MAX_POINTS else "."))
    return (drawn,)


@app.function
def cross(o, a, b):
    # > 0: o → a → b turns left. < 0: it turns right. 0: all three on one line.
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


@app.function
def svg_canvas(body):
    # Shared frame for all three views: drawdata pixels (y up) onto an SVG (y down).
    scale, margin = 0.7, 12
    size_x, size_y = WIDTH * scale + 2 * margin, HEIGHT * scale + 2 * margin

    def xy(p):
        return margin + p[0] * scale, margin + (HEIGHT - p[1]) * scale

    return (
        f'<svg width="{size_x:.0f}" height="{size_y:.0f}" viewBox="0 0 {size_x:.0f} {size_y:.0f}">'
        f'<rect width="{size_x:.0f}" height="{size_y:.0f}" rx="8" fill="#f8fafc"/>'
        + body(xy)
        + "</svg>"
    )


@app.function
def chain(xy, pts, stroke, width, extra="", closed=False, fill="none"):
    # A run of points joined by lines, in a single <path> to keep each stored view small.
    if len(pts) < 2:
        return ""
    d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in map(xy, pts)) + ("Z" if closed else "")
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" fill="{fill}" {extra}/>'


@app.function
def dots(xy, pts, fill, size):
    # Zero-length segments with round caps draw as dots, all in one <path>.
    d = "".join(f"M{x:.1f},{y:.1f}h0" for x, y in map(xy, pts))
    if not d:
        return ""
    return f'<path d="{d}" stroke="{fill}" stroke-width="{size}" stroke-linecap="round"/>'


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Monotone chain: keep the left turns

    Sort the points left to right and build the bottom of the hull on a stack. Each
    new point (**blue**) is checked against the last two on the stack. A right turn
    (**red**) means the middle point is inside the hull, so it's popped. Then do the
    same right to left for the top. Timeline: points on the stacks.
    """)
    return


@app.function
def monotone_chain(points):
    pts = sorted(points)
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()  # lower[-1] is inside: not on the hull
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    # Each chain ends where the other begins; drop the copies.
    return lower[:-1] + upper[:-1]


@app.function
def chain_view(points, lower=(), upper=None, p=None):
    # Whichever stack the loop is working on.
    stack = lower if upper is None else upper

    def body(xy):
        parts = [dots(xy, points, "#94a3b8", 8)]
        if upper is not None:
            parts.append(chain(xy, lower, "#94a3b8", 3))
        parts.append(chain(xy, stack, "#0f172a", 4))
        if p is not None and (not stack or stack[-1] != p):
            if len(stack) >= 2 and cross(stack[-2], stack[-1], p) <= 0:
                # A right turn: the middle point is about to be popped.
                parts.append(chain(xy, [stack[-2], stack[-1], p], "#dc2626", 4, 'stroke-dasharray="8 6"'))
                parts.append(dots(xy, [stack[-1]], "#dc2626", 14))
            elif stack:
                parts.append(chain(xy, [stack[-1], p], "#2563eb", 4, 'stroke-dasharray="8 6"'))
        parts.append(dots(xy, stack, "#0f172a", 10))
        if p is not None:
            parts.append(dots(xy, [p], "#2563eb", 14))
        return "".join(parts)

    return svg_canvas(body)


@app.cell
def _(drawn):
    chain_viewer = mo.ui.anywidget(
        StateViewer(
            monotone_chain,
            chain_view,
            args=(drawn,),
            only_changes=True,
            timeline_func=lambda lower=(), upper=(): len(lower) + len(upper),
            timeline_label="points on the stacks",
            variables=["p", "lower", "upper"],
        )
    )
    chain_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Gift wrapping: walk around the outside

    Start at the leftmost point, which must be on the hull. Guess any next point
    (**blue**), then check every other point (**orange**). Whenever one lies to the
    right of the guess, it becomes the new guess. When the scan ends, nothing is
    further right, so the guess is the next hull point. Repeat until back at the
    start. Timeline: hull points found.
    """)
    return


@app.function
def gift_wrap(points):
    start = min(points)
    hull = []
    current = start
    while True:
        hull.append(current)
        best = points[0]
        for q in points:
            turn = cross(current, best, q)
            # On a tie (all three on one line), take the farther one.
            farther = math.dist(current, q) > math.dist(current, best)
            if best == current or turn < 0 or (turn == 0 and farther):
                best = q
        current = best
        if current == start:
            break
    return hull


@app.function
def wrap_view(points, hull=(), current=None, best=None, q=None):
    def body(xy):
        # Back at the start: the walk is done and the hull closes.
        closed = len(hull) > 2 and current == hull[0]
        parts = [
            dots(xy, points, "#94a3b8", 8),
            chain(xy, list(hull) + ([current] if current is not None and not closed else []), "#0f172a", 4, closed=closed),
        ]
        if not closed and current is not None:
            if q is not None and q != current:
                parts.append(chain(xy, [current, q], "#fb923c", 2.5, 'stroke-dasharray="6 5"'))
            if best is not None and best != current:
                parts.append(chain(xy, [current, best], "#2563eb", 4))
                parts.append(dots(xy, [best], "#2563eb", 14))
        parts.append(dots(xy, hull, "#0f172a", 10))
        if not closed and q is not None and q != current:
            parts.append(dots(xy, [q], "#fb923c", 12))
        if current is not None:
            parts.append(dots(xy, [current], "#0f172a", 14))
        return "".join(parts)

    return svg_canvas(body)


@app.cell(expand_output=True)
def _(drawn):
    wrap_viewer = mo.ui.anywidget(
        StateViewer(
            gift_wrap,
            wrap_view,
            args=(drawn,),
            only_changes=True,
            timeline_func=lambda hull: len(hull),
            timeline_label="hull points",
            variables=["current", "best", "q", "turn", "hull"],
        )
    )
    wrap_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Quickhull: divide and conquer

    The leftmost and rightmost points are on the hull. Their line (**blue**) splits
    the rest into an upper and a lower half. In each half, the point farthest from
    the line is on the hull too (**orange**). Everything inside the triangle it makes
    is out. Recurse on the two sides of the triangle. Timeline: call depth.
    """)
    return


@app.function
def quickhull(points, a=None, b=None, hull=None):
    if a is None:
        # First call: split by the line from leftmost to rightmost.
        a, b = min(points), max(points)
        hull = [a, b]
        above = [p for p in points if cross(a, b, p) > 0]
        below = [p for p in points if cross(b, a, p) > 0]
        quickhull(above, a, b, hull)
        quickhull(below, b, a, hull)
        return hull
    # Later calls: `points` lie left of a → b. Hull them.
    if not points:
        return hull
    far = max(points, key=lambda p: cross(a, b, p))
    hull.append(far)
    # Only points outside triangle a, far, b can be on the hull.
    outside_a = [p for p in points if cross(a, far, p) > 0]
    outside_b = [p for p in points if cross(far, b, p) > 0]
    quickhull(outside_a, a, far, hull)
    quickhull(outside_b, far, b, hull)
    return hull


@app.function
def around_centre(pts):
    # A convex polygon's corners, in order: sort them by angle around their mean.
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


@app.function
def quickhull_view(drawn, points=(), a=None, b=None, far=None, hull=()):
    # `points` is only this call's share; `drawn` is all of them, for context.
    hull = hull or ()  # None until the first call sets it up
    def body(xy):
        parts = []
        if len(hull) > 2:
            parts.append(chain(xy, around_centre(hull), "#0f172a", 3, closed=True, fill="#e2e8f0"))
        parts.append(dots(xy, drawn, "#cbd5e1", 8))
        parts.append(dots(xy, points, "#475569", 9))
        if a is not None and b is not None:
            parts.append(chain(xy, [a, b], "#2563eb", 4))
            if far is not None:
                parts.append(chain(xy, [a, far, b], "#fb923c", 3, 'stroke-dasharray="8 6"'))
        parts.append(dots(xy, hull, "#0f172a", 12))
        if far is not None:
            parts.append(dots(xy, [far], "#fb923c", 14))
        return "".join(parts)

    return svg_canvas(body)


@app.cell
def _(drawn):
    quickhull_viewer = mo.ui.anywidget(
        StateViewer(
            quickhull,
            # Nested calls only see their own `points`, so hand the view all of them.
            functools.partial(quickhull_view, drawn),
            args=(drawn,),
            only_changes=True,
            variables=["a", "b", "far", "hull"],
        )
    )
    quickhull_viewer
    return


@app.cell(hide_code=True)
def _(drawn):
    hulls = {
        "Monotone chain": monotone_chain(drawn),
        "Gift wrapping": gift_wrap(drawn),
        "Quickhull": quickhull(drawn),
    }
    same = len({frozenset(hull) for hull in hulls.values()}) == 1
    lines = ["## Same hull, different route", "", "| | hull points |", "| --- | --- |"]
    lines += [f"| {name} | {len(hull)} |" for name, hull in hulls.items()]
    lines += ["", "All three find the same corners." if same else "The three disagree, which is a bug."]
    mo.md("\n".join(lines))
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Which one is faster?

    The same three functions race on two kinds of point clouds, from 100 up to
    409,600 points:

    - **square**: spread evenly over a square. Only a few dozen end up on the hull.
    - **circle**: all on a circle, so *every* point is a hull point.

    Plus scipy's `ConvexHull` (Qhull, written in C) as a yardstick. Anything slower
    than half a second per run drops out. Takes ~20 s, so it waits for the button.
    """)
    return


@app.function
def square_points(n, seed):
    rng = random.Random(seed)
    return [(rng.random(), rng.random()) for _ in range(n)]


@app.function
def circle_points(n, seed):
    rng = random.Random(seed)
    angles = [rng.uniform(0, 2 * math.pi) for _ in range(n)]
    return [(math.cos(t), math.sin(t)) for t in angles]


@app.cell
def _():
    run_benchmark = mo.ui.run_button(label="Run the benchmark")
    run_benchmark
    return (run_benchmark,)


@app.cell
def _(run_benchmark):
    mo.stop(not run_benchmark.value, mo.md("*Press the button above to run the benchmark.*"))
    contenders = {
        "Monotone chain": monotone_chain,
        "Gift wrapping": gift_wrap,
        "Quickhull": quickhull,
        "scipy (Qhull)": lambda pts: ConvexHull(pts).vertices,
    }
    shapes = {"square": square_points, "circle": circle_points}
    # 100, 200, 400, ... doubling up to 409,600 points.
    sizes = [100 * 2**i for i in range(13)]
    rows = []
    # marimo runs cells under a debugger hook (sys.settrace) that taxes every
    # Python call, so switch it off while timing and put it back afterwards.
    previous_trace = sys.gettrace()
    sys.settrace(None)
    with mo.status.progress_bar(total=len(shapes) * len(sizes), title="Benchmarking", remove_on_exit=True) as bar:
        for shape, make in shapes.items():
            # A contender that needs over half a second sits out the bigger sizes.
            too_slow = set()
            for n in sizes:
                bar.update(increment=0, subtitle=f"{shape}, {n:,} points")
                pts = make(n, 0)
                hull_size = len(monotone_chain(pts))
                for name, run in contenders.items():
                    if name in too_slow:
                        continue
                    # Best of three, so a hiccup on the machine doesn't count.
                    seconds = min(timeit.repeat(lambda: run(pts), number=1, repeat=3))
                    rows.append({"shape": shape, "points": n, "hull points": hull_size, "algorithm": name, "ms": seconds * 1000})
                    if seconds > 0.5:
                        too_slow.add(name)
                bar.update()
    sys.settrace(previous_trace)
    return (rows,)


@app.cell
def _(rows):
    def panel(shape):
        return (
            alt.Chart(alt.Data(values=[row for row in rows if row["shape"] == shape]))
            .mark_line(point=True)
            .encode(
                x=alt.X("points:Q", scale=alt.Scale(type="log"), title="points"),
                y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="milliseconds (best of 3)"),
                color=alt.Color("algorithm:N", title=None),
                tooltip=["algorithm:N", "points:Q", "hull points:Q", alt.Tooltip("ms:Q", format=".2f")],
            )
            .properties(title=f"points in a {shape}", width=300, height=280)
            # Scroll to zoom, drag to pan, double-click to reset. A name per
            # panel keeps the two zooms independent.
            .add_params(alt.selection_interval(bind="scales", name=f"zoom_{shape}"))
        )

    # One row per shape and size with a column per algorithm, so the numbers line up.
    wide = {}
    for row in rows:
        key = (row["shape"], row["points"])
        wide.setdefault(key, {"shape": row["shape"], "points": row["points"], "hull points": row["hull points"]})[row["algorithm"]] = round(row["ms"], 2)
    mo.vstack([
        alt.hconcat(panel("square"), panel("circle")),
        mo.accordion({"All timings": mo.ui.table(list(wide.values()), selection=None, page_size=13)}),
    ])
    return


@app.cell(hide_code=True)
def _(rows):
    # Takes `rows` so this only shows up once the benchmark has run.
    mo.md("""
    - **Square:** past ~1,000 points Quickhull is the fastest of the three. Its first split already
      throws away most points as inside. Gift wrapping scans all n points once
      per hull point, but with only ~25 hull points that's just ~6× slower.
    - **Circle:** now every point is a hull point, so gift wrapping's scans add up
      to n² and it drops out around 3,200 points. Quickhull's triangles no longer
      discard anything, so it slows down too. Monotone chain doesn't care: it's a
      sort and two passes either way, and here it even beats Qhull (~310 ms
      against ~480 ms at 409,600 points).

    Few points on the hull: throw the inside away early (Quickhull). Many points on
    the hull: sort and sweep (monotone chain). Gift wrapping costs n × hull points,
    so even a tiny hull leaves it trailing; its strength is being easy to follow.
    """)
    return


if __name__ == "__main__":
    app.run()
