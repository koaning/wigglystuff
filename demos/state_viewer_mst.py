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

__generated_with = "0.25.1"
app = marimo.App(width="medium")

with app.setup:
    import heapq
    import math
    import random
    import sys
    import timeit

    import altair as alt
    import marimo as mo
    from scipy.spatial import Delaunay

    from wigglystuff import StateViewer


@app.cell(hide_code=True)
def _():
    mo.md("""
    # Growing a minimum spanning tree

    Connect every pair of points. The cheapest set of lines that still links them
    all is the *minimum spanning tree*. Two classic ways to grow one:

    - **Prim**: grow one tree outward from a start point.
    - **Kruskal**: take edges shortest-first, merging small trees into one.

    Press play, or drag the timeline to scrub.
    """)
    return


@app.function
def make_points(n, seed):
    rng = random.Random(seed)
    return [(rng.random(), rng.random()) for _ in range(n)]


@app.function
def dist(points, i, j):
    return math.dist(points[i], points[j])


@app.cell
def _():
    n_points = mo.ui.slider(5, 20, value=12, label="points", show_value=True, debounce=True)
    seed = mo.ui.number(start=0, stop=999, value=4, label="seed")
    mo.hstack([n_points, seed], justify="start", gap=2)
    return n_points, seed


@app.cell
def _(n_points, seed):
    points = make_points(n_points.value, seed.value)
    # Every point neighbours every point (itself included; the algorithms skip it).
    complete = [range(len(points))] * len(points)
    return complete, points


@app.function
def svg_canvas(points, body):
    # Shared frame for both views: points live in the unit square and get
    # mapped onto a fixed-size canvas with a margin.
    size, margin = 420, 24
    xy = [(margin + x * (size - 2 * margin), margin + y * (size - 2 * margin)) for x, y in points]
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<rect width="{size}" height="{size}" rx="8" fill="#f8fafc"/>'
        + body(xy)
        + "</svg>"
    )


@app.function
def edge_path(xy, edges, stroke, width, extra=""):
    # All edges of one style in a single <path> keeps each stored view small.
    d = "".join(f"M{xy[a][0]:.1f},{xy[a][1]:.1f}L{xy[b][0]:.1f},{xy[b][1]:.1f}" for a, b in edges)
    if not d:
        return ""
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" fill="none" {extra}/>'


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Prim: one tree grows outward

    Pop the cheapest edge leaving the tree (**blue**), add its far end, push that
    point's edges (**orange**). Stale edges get skipped (**red**).
    Timeline: heap size.
    """)
    return


@app.function
def prim(points, neighbours, start):
    in_tree = {start}
    tree = []
    heap = [(dist(points, start, w), start, w) for w in neighbours[start] if w != start]
    heapq.heapify(heap)
    while heap and len(in_tree) < len(points):
        weight, u, v = heapq.heappop(heap)
        if v in in_tree:
            continue  # stale entry: v joined the tree through a cheaper edge
        tree.append((u, v))
        in_tree.add(v)
        for w in neighbours[v]:
            if w not in in_tree:
                heapq.heappush(heap, (dist(points, v, w), v, w))
    return tree


@app.function
def prim_view(points, start, tree=(), in_tree=(), heap=(), u=None, v=None):
    in_tree = in_tree or {start}

    def body(xy):
        # Live candidates only: heap entries whose far end is still outside the tree.
        candidates = {(a, b) for _, a, b in heap if b not in in_tree}
        parts = [
            edge_path(xy, candidates, "#fb923c", 1.5, 'opacity="0.55"'),
            edge_path(xy, tree, "#0f172a", 4),
        ]
        # The popped edge: blue while it's being added (and while its point's
        # edges get pushed), red dashed when it turns out to be stale.
        if u is not None:
            stale = v in in_tree and (u, v) not in tree
            parts.append(
                edge_path(xy, [(u, v)], "#dc2626" if stale else "#2563eb", 6,
                          'stroke-dasharray="8 6"' if stale else "")
            )
        for i, (x, y) in enumerate(xy):
            fill = "#0f172a" if i in in_tree else "#ffffff"
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{fill}" stroke="#0f172a" stroke-width="2"/>'
            )
        return "".join(parts)

    return svg_canvas(points, body)


@app.cell
def _(complete, points):
    prim_viewer = mo.ui.anywidget(
        StateViewer(
            prim,
            prim_view,
            args=(points, complete, 0),
            timeline_func=lambda heap: len(heap),
            timeline_label="heap size",
            variables=["weight", "u", "v", "in_tree", "tree"],
        )
    )
    prim_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Kruskal: a forest merges

    Walk the edges shortest-first. Keep one that joins two fragments, skip one that
    would close a cycle (**red**). Timeline: number of fragments.
    """)
    return


@app.function
def find(parent, i):
    while parent[i] != i:
        # Path halving: point i at its grandparent on the way up, so later
        # finds walk shorter chains. Without it, big graphs get slow.
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


@app.function
def kruskal(points, neighbours):
    n = len(points)
    # i < j so each edge is listed once, not once from each end.
    edges = sorted((dist(points, i, j), i, j) for i in range(n) for j in neighbours[i] if i < j)
    parent = list(range(n))
    tree = []
    for weight, u, v in edges:
        ru, rv = find(parent, u), find(parent, v)
        if ru == rv:
            continue  # already connected: this edge would close a cycle
        tree.append((u, v))
        parent[ru] = rv
        if len(tree) == n - 1:
            break
    return tree


@app.function
def components(parent):
    # find() rewires parent as it goes, so work on a copy, not the live run.
    parent = list(parent)
    return len({find(parent, i) for i in range(len(parent))})


@app.function
def kruskal_view(points, tree=(), parent=None, u=None, v=None):
    palette = ["#2563eb", "#16a34a", "#9333ea", "#ea580c", "#0891b2",
               "#db2777", "#65a30d", "#ca8a04", "#4f46e5", "#0d9488"]
    # A copy, because find() rewires parent and the view must not touch the run.
    parent = list(parent) if parent else list(range(len(points)))
    roots = [find(parent, i) for i in range(len(points))]
    sizes = {r: roots.count(r) for r in roots}

    def body(xy):
        parts = []
        # Tree edges take the colour of the fragment they belong to.
        for root in sizes:
            edges = [(a, b) for a, b in tree if roots[a] == root]
            parts.append(edge_path(xy, edges, palette[root % len(palette)], 4))
        if u is not None and (u, v) not in tree:
            cycle = roots[u] == roots[v]
            parts.append(
                edge_path(xy, [(u, v)], "#dc2626" if cycle else "#0f172a", 5,
                          'stroke-dasharray="8 6"' if cycle else 'opacity="0.6"')
            )
        for i, (x, y) in enumerate(xy):
            fill = "#cbd5e1" if sizes[roots[i]] == 1 else palette[roots[i] % len(palette)]
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{fill}" stroke="#0f172a" stroke-width="2"/>'
            )
        return "".join(parts)

    return svg_canvas(points, body)


@app.cell
def _(complete, points):
    kruskal_viewer = mo.ui.anywidget(
        StateViewer(
            kruskal,
            kruskal_view,
            args=(points, complete),
            timeline_func=components,
            variables=["weight", "u", "v", "ru", "rv", "tree"],
        )
    )
    kruskal_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Or use the geometry

    If some point is closer to *both* ends of an edge, that edge is the longest side
    of a triangle. Going around the other two sides is cheaper, so the MST never
    needs it.

    1. **Prune**: for each pair (**blue**), look for such a point (**orange**).
       Found one? The pair is out (**red**).
    2. **Kruskal** on the few edges that are left.
    """)
    return


@app.function
def pruned_mst(points):
    n = len(points)
    # 1. Keep an edge only if no other point is closer to both of its ends.
    keep = []
    for p in range(n):
        for q in range(p + 1, n):
            blocker = next(
                (r for r in range(n) if r not in (p, q) and max(dist(points, p, r), dist(points, q, r)) < dist(points, p, q)),
                None,
            )
            if blocker is None:
                keep.append((p, q))
    # 2. Kruskal, but only on the edges that are left.
    edges = sorted((dist(points, a, b), a, b) for a, b in keep)
    parent = list(range(n))
    tree = []
    for weight, u, v in edges:
        ru, rv = find(parent, u), find(parent, v)
        if ru == rv:
            continue  # already connected: this edge would close a cycle
        tree.append((u, v))
        parent[ru] = rv
        if len(tree) == n - 1:
            break
    return tree


@app.function
def pruned_view(points, keep=(), p=None, q=None, tree=(), parent=None, u=None, v=None):
    kruskal_phase = parent is not None

    def body(xy):
        parts = [edge_path(xy, keep, "#cbd5e1" if kruskal_phase else "#64748b", 2)]
        if kruskal_phase:
            parts.append(edge_path(xy, tree, "#0f172a", 4))
            if u is not None:
                cycle = (u, v) not in tree and find(list(parent), u) == find(list(parent), v)
                parts.append(
                    edge_path(xy, [(u, v)], "#dc2626" if cycle else "#2563eb", 6,
                              'stroke-dasharray="8 6"' if cycle else "")
                )
        elif p is not None and q is not None and q < len(points):
            # Worked out here rather than read from `blocker`, which still holds
            # the previous pair's answer until its line runs.
            blocker = next(
                (r for r in range(len(points)) if r not in (p, q)
                 and max(dist(points, p, r), dist(points, q, r)) < dist(points, p, q)),
                None,
            )
            if blocker is None:
                parts.append(edge_path(xy, [(p, q)], "#2563eb", 5))
            else:
                parts.append(edge_path(xy, [(p, q)], "#dc2626", 4, 'stroke-dasharray="8 6"'))
                parts.append(edge_path(xy, [(p, blocker), (q, blocker)], "#fb923c", 3))
                bx, by = xy[blocker]
                parts.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="10" fill="#fb923c"/>')
        for x, y in xy:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#0f172a"/>')
        return "".join(parts)

    return svg_canvas(points, body)


@app.function
def pruned_progress(keep=(), tree=()):
    # Kept edges while pruning, then tree edges on top while Kruskal runs.
    return len(keep) + len(tree)


@app.cell
def _(points):
    pruned_viewer = mo.ui.anywidget(
        StateViewer(
            pruned_mst,
            pruned_view,
            args=(points,),
            only_changes=True,
            timeline_func=pruned_progress,
            timeline_label="kept + tree edges",
            variables=["p", "q", "blocker", "weight", "u", "v", "tree"],
        )
    )
    pruned_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    Checking every pair against every point is slow (n³). The surviving edges always
    sit on the Delaunay triangulation, which scipy builds fast, so the benchmark uses
    that instead.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## Which one is faster?

    The same functions race on two graphs:

    - **complete**: every pair linked, up to 1,600 points
    - **sparse**: 6 nearest neighbours each, up to 102,400 points

    Plus **Prim without a heap** (a plain list of the cheapest edge to each point,
    scanned every round) and, on the complete graph, the geometry routes:
    **Pruning + Kruskal** from above and **Delaunay + Kruskal** (scipy).
    Anything slower than half a second per run drops out. Takes ~35 s, so it waits
    for the button.
    """)
    return


@app.function
def prim_no_heap(points, neighbours, start):
    n = len(points)
    best = [math.inf] * n  # cheapest known edge from the tree to each point
    link = [None] * n  # the tree point at the other end of that edge
    best[start] = 0
    in_tree = [False] * n
    tree = []
    for _ in range(n):
        v = min((i for i in range(n) if not in_tree[i]), key=best.__getitem__)
        in_tree[v] = True
        if link[v] is not None:
            tree.append((link[v], v))
        for w in neighbours[v]:
            if not in_tree[w]:
                d = dist(points, v, w)
                if d < best[w]:
                    best[w], link[w] = d, v
    return tree


@app.function
def nearest_neighbours(points, k):
    # Link each point to its k nearest points, and back, so the graph is undirected.
    # Checking all n points for each point would cost n², so first drop the points
    # into a grid with about 2 per cell and only look in the 5×5 block of cells
    # around each point. That block almost always holds the true k nearest.
    n = len(points)
    side = max(1, int(math.sqrt(n / 2)))
    cells = {}
    for i, (x, y) in enumerate(points):
        cells.setdefault((int(x * side), int(y * side)), []).append(i)
    neighbours = [set() for _ in range(n)]
    for i, (x, y) in enumerate(points):
        cx, cy = int(x * side), int(y * side)
        nearby = [
            j
            for dx in range(-2, 3)
            for dy in range(-2, 3)
            for j in cells.get((cx + dx, cy + dy), ())
            if j != i
        ]
        for j in heapq.nsmallest(k, nearby, key=lambda j: dist(points, i, j)):
            neighbours[i].add(j)
            neighbours[j].add(i)
    return [sorted(linked) for linked in neighbours]


@app.function
def scipy_delaunay_neighbours(points):
    # Delaunay triangulation from scipy (in C); it holds every MST edge.
    neighbours = [set() for _ in points]
    for a, b, c in Delaunay(points).simplices.tolist():
        neighbours[a] |= {b, c}
        neighbours[b] |= {a, c}
        neighbours[c] |= {a, b}
    return [sorted(linked) for linked in neighbours]


@app.cell
def _():
    run_benchmark = mo.ui.run_button(label="Run the benchmark")
    run_benchmark
    return (run_benchmark,)


@app.cell
def _(run_benchmark):
    mo.stop(not run_benchmark.value, mo.md("*Press the button above to run the benchmark.*"))
    contenders = {
        "Prim (heap)": lambda pts, nb: prim(pts, nb, 0),
        "Kruskal": kruskal,
        "Prim (no heap)": lambda pts, nb: prim_no_heap(pts, nb, 0),
        # Ignores the complete graph and triangulates instead; same tree.
        "Delaunay + Kruskal": lambda pts, nb: kruskal(pts, scipy_delaunay_neighbours(pts)),
        # The pruning from above: also ignores the complete graph, same tree.
        "Pruning + Kruskal": lambda pts, nb: pruned_mst(pts),
    }
    sizes = {
        # n²/2 edges: past 1600 points this gets slow and memory hungry.
        "complete": [50, 100, 200, 400, 800, 1600],
        # 50, 100, 200, ... doubling up to 102,400 points.
        "sparse": [50 * 2**i for i in range(12)],
    }
    rows = []
    # marimo runs cells under a debugger hook (sys.settrace) that taxes every
    # Python call, so switch it off while timing and put it back afterwards.
    previous_trace = sys.gettrace()
    sys.settrace(None)
    # One tick per graph and size: 18 in all.
    n_ticks = sum(len(graph_sizes) for graph_sizes in sizes.values())
    with mo.status.progress_bar(total=n_ticks, title="Benchmarking", remove_on_exit=True) as bar:
        for graph, graph_sizes in sizes.items():
            # A contender that needs over half a second sits out the bigger sizes.
            too_slow = set()
            for n in graph_sizes:
                pts = make_points(n, 0)
                bar.update(increment=0, subtitle=f"{graph} graph, {n:,} points")
                nb = [range(n)] * n if graph == "complete" else nearest_neighbours(pts, 6)
                for name, run in contenders.items():
                    # Delaunay and pruning only stand in for the complete graph: the
                    # sparse graph's own MST can use edges they'd never offer.
                    if name in too_slow or (graph == "sparse" and name in ("Delaunay + Kruskal", "Pruning + Kruskal")):
                        continue
                    # A 6-nearest-neighbour graph can in principle fall apart into
                    # islands; then there is no spanning tree to compare.
                    if graph == "sparse":
                        assert len(run(pts, nb)) == n - 1, f"sparse graph at {n} points is disconnected"
                    # Best of three, so a hiccup on the machine doesn't count.
                    seconds = min(timeit.repeat(lambda: run(pts, nb), number=1, repeat=3))
                    rows.append({"graph": graph, "points": n, "algorithm": name, "ms": seconds * 1000})
                    if seconds > 0.5:
                        too_slow.add(name)
                bar.update()
    sys.settrace(previous_trace)
    return (rows,)


@app.cell
def _(rows):
    def panel(graph):
        return (
            alt.Chart(alt.Data(values=[row for row in rows if row["graph"] == graph]))
            .mark_line(point=True)
            .encode(
                x=alt.X("points:Q", scale=alt.Scale(type="log"), title="points"),
                y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="milliseconds (best of 3)"),
                color=alt.Color("algorithm:N", title=None),
                tooltip=["algorithm:N", "points:Q", alt.Tooltip("ms:Q", format=".2f")],
            )
            .properties(title=f"{graph} graph", width=300, height=280)
            # Scroll to zoom, drag to pan, double-click to reset. A name per
            # panel keeps the two zooms independent.
            .add_params(alt.selection_interval(bind="scales", name=f"zoom_{graph}"))
        )

    # One row per graph and size with a column per algorithm, so the numbers line up.
    wide = {}
    for row in rows:
        key = (row["graph"], row["points"])
        wide.setdefault(key, {"graph": row["graph"], "points": row["points"]})[row["algorithm"]] = round(row["ms"], 2)
    mo.vstack([
        alt.hconcat(panel("complete"), panel("sparse")),
        mo.accordion({"All timings": mo.ui.table(list(wide.values()), selection=None, page_size=12)}),
    ])
    return


@app.cell(hide_code=True)
def _():
    # Takes `rows` so this only shows up once the benchmark has run.
    mo.md("""
    - **Complete graph:** no-heap Prim wins. Each edge is one list update for it. The
      heap version pushes 1.28M edges at 1,600 points to use 1,599; Kruskal sorts
      them all first.
    - **Sparse graph:** no-heap Prim still scans all n points each round, so it
      drops out early. Heap Prim and Kruskal tie.
    - **Points on a plane:** skip the complete graph. Delaunay + Kruskal finds the
      same tree at 1,600 points in ~6 ms, against ~160 ms for the best of the rest.
      Pruning gets the same few edges, but checking every pair against every point
      makes it the slowest of all.

    Dense graph: scan a list. Sparse graph: use a heap or a sort.
    """)
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    ## When does Kruskal win?

    **1. Islands.** Prim stops at the edge of its own island. Kruskal returns one
    tree per island, for free.
    """)
    return


@app.function
def graph_view(points, neighbours, tree, reached):
    links = [(i, j) for i, linked in enumerate(neighbours) for j in linked if i < j]

    def body(xy):
        parts = [
            edge_path(xy, links, "#cbd5e1", 1.5),
            edge_path(xy, tree, "#0f172a", 3),
        ]
        for i, (x, y) in enumerate(xy):
            fill = "#0f172a" if i in reached else "#ffffff"
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{fill}" stroke="#0f172a" stroke-width="1.5"/>'
            )
        return "".join(parts)

    return svg_canvas(points, body)


@app.cell
def _():
    island_k = mo.ui.slider(1, 6, value=2, label="neighbours per point", show_value=True)
    island_k
    return (island_k,)


@app.cell
def _(island_k):
    island_points = make_points(150, 4)
    island_graph = nearest_neighbours(island_points, island_k.value)
    island_prim = prim(island_points, island_graph, 0)
    island_kruskal = kruskal(island_points, island_graph)
    prim_reached = {0} | {p for edge in island_prim for p in edge}
    # A forest over n points with e edges has n - e trees.
    n_islands = len(island_points) - len(island_kruskal)
    mo.hstack(
        [
            mo.vstack([
                mo.md(f"**Prim** reaches {len(prim_reached)} of {len(island_points)} points"),
                mo.Html(graph_view(island_points, island_graph, island_prim, prim_reached)),
            ]),
            mo.vstack([
                mo.md(f"**Kruskal** spans all {n_islands} island{'s' if n_islands > 1 else ''}"),
                mo.Html(graph_view(island_points, island_graph, island_kruskal, range(len(island_points)))),
            ]),
        ],
        justify="start",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md("""
    **2. Many points, medium density.** At 51,200 points with 12+ neighbours each,
    Kruskal is 10–20% faster. At 25,600 they tie, so it's a narrow win.
    """)
    return


@app.cell
def _(run_benchmark):
    mo.stop(not run_benchmark.value, mo.md("*Press the button above to run this one too.*"))
    sweep_points = make_points(51_200, 0)
    sweep_rows = []
    # Same trick as above: no debugger hook while timing.
    previous_sweep_trace = sys.gettrace()
    sys.settrace(None)
    with mo.status.progress_bar(total=3, title="Neighbour sweep", remove_on_exit=True) as sweep_bar:
        for k in [6, 12, 24]:
            sweep_bar.update(increment=0, subtitle=f"{k} neighbours per point")
            sweep_graph = nearest_neighbours(sweep_points, k)
            for _name, _run in {
                "Prim (heap)": lambda: prim(sweep_points, sweep_graph, 0),
                "Kruskal": lambda: kruskal(sweep_points, sweep_graph),
            }.items():
                _seconds = min(timeit.repeat(_run, number=1, repeat=3))
                sweep_rows.append({"neighbours": k, "algorithm": _name, "ms": _seconds * 1000})
            sweep_bar.update()
    sys.settrace(previous_sweep_trace)
    (
        alt.Chart(alt.Data(values=sweep_rows))
        .mark_line(point=True)
        .encode(
            x=alt.X("neighbours:Q", title="neighbours per point (51,200 points)"),
            y=alt.Y("ms:Q", title="milliseconds (best of 3)"),
            color=alt.Color("algorithm:N", title=None),
            tooltip=["algorithm:N", "neighbours:Q", alt.Tooltip("ms:Q", format=".1f")],
        )
        .properties(width=520, height=280)
        .add_params(alt.selection_interval(bind="scales", name="zoom_sweep"))
    )
    return


@app.cell(hide_code=True)
def _(complete, points):
    trees = {
        "Prim": prim(points, complete, 0),
        "Kruskal": kruskal(points, complete),
        "Pruning + Kruskal": pruned_mst(points),
    }
    same = len({frozenset(frozenset(e) for e in tree) for tree in trees.values()}) == 1
    lines = ["## Same tree, different route", "", "| | total length |", "| --- | --- |"]
    lines += [f"| {name} | {sum(dist(points, a, b) for a, b in tree):.4f} |" for name, tree in trees.items()]
    lines += ["", "All three find the same tree; only the order differs." if same else "Equally cheap trees, different edges."]
    mo.md("\n".join(lines))
    return


if __name__ == "__main__":
    app.run()
