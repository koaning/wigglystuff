# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "altair",
#     "marimo",
#     "numpy",
#     "pillow",
#     "scikit-learn",
#     "wigglystuff==0.5.40",
# ]
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    layout_file="layouts/state_viewer_emeans.slides.json",
)

with app.setup:
    import math
    import random

    import altair as alt
    import marimo as mo

    from wigglystuff import EsmWidget, ScatterWidget, StateViewer

    # The drawing area, in drawdata pixels. Views draw it at 0.7x.
    WIDTH, HEIGHT = 600, 400
    # More points means more batches, and more steps in every viewer.
    MAX_POINTS = 150
    # One colour per cluster.
    PALETTE = ["#2563eb", "#ea580c", "#16a34a", "#9333ea", "#db2777", "#0891b2", "#ca8a04", "#4b5563"]


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # k-means vs e-means

    Two algorithms for the same job: place $k$ centroids so every point has one nearby.
    Both assign points to their nearest centroid. **k-means** does that for *every*
    point; **e-means** ([Bessa et al., 2026](https://arxiv.org/abs/2611.09501)) for a
    batch of $B$ points, and also takes the sum and count over just that batch. Then:

    $$
    \begin{aligned}
    & \textbf{k-means} && \textbf{e-means} \\[0.5em]
    \text{sum}_j &\leftarrow \text{all points in } j \text{, added up} \qquad\qquad
      & \text{sum}_j &\leftarrow (1-\alpha)\,\text{sum}_j + \alpha\,\text{batch sum}_j \\
    \text{count}_j &\leftarrow \text{number of points in } j
      & \text{count}_j &\leftarrow (1-\alpha)\,\text{count}_j + \alpha\,\text{batch count}_j \\
    c_j &\leftarrow \text{sum}_j \,/\, \text{count}_j
      & c_j &\leftarrow \text{sum}_j \,/\, \text{count}_j
    \end{aligned}
    $$

    Draw some points, then watch both.
    """)
    return


@app.function(hide_code=True)
def seed_points(seed):
    # Four blobs: (centre x, centre y, spread, number of points). drawdata stores
    # pixels with y pointing up, and wants a colour per point.
    rng = random.Random(seed)
    blobs = [(130, 290, 30, 30), (420, 300, 45, 25), (300, 110, 30, 25), (500, 110, 20, 15)]
    return [
        {"x": rng.gauss(cx, spread), "y": rng.gauss(cy, spread), "color": "#1f77b4", "label": "a", "batch": 0}
        for cx, cy, spread, count in blobs
        for _ in range(count)
    ]


@app.cell(hide_code=True)
def _():
    draw = mo.ui.anywidget(
        ScatterWidget(n_classes=1, width=WIDTH, height=HEIGHT, brushsize=25, data=seed_points(1))
    )
    draw
    return (draw,)


@app.cell(hide_code=True)
def _(draw):
    # Whole pixels keep the variable tables short. The brush can drop two points
    # on the same pixel; keep each only once.
    drawn = sorted({(round(d["x"]), round(d["y"])) for d in draw.data})
    if len(drawn) > MAX_POINTS:
        drawn = sorted(random.Random(0).sample(drawn, MAX_POINTS))
    mo.stop(len(drawn) < 10, mo.md("*Draw at least ten points.*"))
    mo.md(f"Clustering **{len(drawn)}** points" + (f" (a sample of {MAX_POINTS})." if len(draw.data) > MAX_POINTS else "."))
    return (drawn,)


@app.function(hide_code=True)
def dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


@app.function(hide_code=True)
def nearest(p, centroids):
    # Index of the centroid closest to p.
    return min(range(len(centroids)), key=lambda j: dist2(p, centroids[j]))


@app.function(hide_code=True)
def mse(points, centroids):
    # The k-means loss: mean squared distance to the nearest centroid.
    return sum(min(dist2(p, c) for c in centroids) for p in points) / len(points)


@app.function(hide_code=True)
def batches(points, batch_size, rng):
    # A fresh shuffle, cut into whole batches. Leftover points sit this epoch out.
    order = list(points)
    rng.shuffle(order)
    return [order[i * batch_size : (i + 1) * batch_size] for i in range(len(points) // batch_size)]


@app.function(hide_code=True)
def cosine_alpha(t, updates, alpha0, floor):
    # Equation 5, for update t = 1, 2, ...: alpha0 at the first, floor * alpha0 at the last.
    # Rounded so the variables table stays readable.
    return round(alpha0 * (floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * (t - 1) / updates))), 3)


@app.function(hide_code=True)
def assign(batch, centroids):
    # (point, cluster) pairs: every point picks its nearest centroid.
    return [(x, nearest(x, centroids)) for x in batch]


@app.function(hide_code=True)
def batch_summary(assigned, k):
    # Per cluster: how many points it got, and their mean (None when it got none).
    counts = [0] * k
    totals = [(0.0, 0.0)] * k
    for x, j in assigned:
        counts[j] += 1
        totals[j] = (totals[j][0] + x[0], totals[j][1] + x[1])
    means = [(tx / n, ty / n) if n else None for (tx, ty), n in zip(totals, counts)]
    return counts, means


@app.function(hide_code=True)
def blend(weights, centroids, counts, means, alpha):
    # The new centroid is a weighted average of the old centroid and the batch mean.
    new_weights, new_centroids = [], []
    for w, c, n, m in zip(weights, centroids, counts, means):
        old, new = (1 - alpha) * w, alpha * n
        if n:  # a cluster that got no points stays where it is
            c = ((old * c[0] + new * m[0]) / (old + new), (old * c[1] + new * m[1]) / (old + new))
        new_weights.append(old + new)
        new_centroids.append(c)
    return new_weights, new_centroids


@app.function(hide_code=True)
def revive(weights, centroids, rng, tau=0.1, nudge=2**-7):
    # Clusters below tau * the average weight take over half of a donor, picked by weight.
    weights, centroids = list(weights), list(centroids)
    k = len(weights)
    threshold = tau * sum(weights) / k
    revived = []
    for j in range(k):
        if weights[j] < threshold:
            donor = rng.choices(range(k), weights=weights)[0]
            x, y = centroids[donor]
            # Two copies of the donor's centroid, nudged apart; one each, half the weight each.
            centroids[j] = (x * (1 + nudge), y * (1 - nudge))
            centroids[donor] = (x * (1 - nudge), y * (1 + nudge))
            weights[donor] = weights[j] = weights[donor] / 2
            revived.append((j, donor))
    return weights, centroids, revived


@app.function(hide_code=True)
def finalize(last_epoch, centroids):
    # Each centroid becomes the mean of its points from the last epoch: one Lloyd update.
    counts, means = batch_summary(last_epoch, len(centroids))
    return [m if m is not None else c for m, c in zip(means, centroids)]


@app.function(hide_code=True)
def e_means(points, centroids, epochs, batch_size, alpha0, floor=0.1, revive_every=5, seed=0):
    rng = random.Random(seed)
    weights = [1e-10] * len(centroids)  # no points behind any centroid yet
    updates = epochs * (len(points) // batch_size)
    t = 0
    for epoch in range(epochs):
        last_epoch = []
        for batch in batches(points, batch_size, rng):
            t += 1
            revived = []
            alpha = cosine_alpha(t, updates, alpha0, floor)
            assigned = assign(batch, centroids)
            counts, means = batch_summary(assigned, len(centroids))
            weights, centroids = blend(weights, centroids, counts, means, alpha)
            last_epoch += assigned
            if revive_every and t % revive_every == 0:
                weights, centroids, revived = revive(weights, centroids, rng)
    return finalize(last_epoch, centroids)


@app.function(hide_code=True)
def initial_centroids(k, seed):
    # Anywhere in the drawing area, not necessarily near a point.
    rng = random.Random(seed)
    return [(rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT)) for _ in range(k)]


@app.function(hide_code=True)
def svg_canvas(body):
    # Shared frame for both views: drawdata pixels (y up) onto an SVG (y down).
    scale, margin = 0.7, 14
    size_x, size_y = WIDTH * scale + 2 * margin, HEIGHT * scale + 2 * margin

    def xy(p):
        return margin + p[0] * scale, margin + (HEIGHT - p[1]) * scale

    return (
        f'<svg width="{size_x:.0f}" height="{size_y:.0f}" viewBox="0 0 {size_x:.0f} {size_y:.0f}">'
        f'<rect width="{size_x:.0f}" height="{size_y:.0f}" rx="8" fill="#f8fafc"/>'
        + body(xy)
        + "</svg>"
    )


@app.function(hide_code=True)
def dots(xy, pts, fill, size, opacity=1.0):
    # Zero-length segments with round caps draw as dots, all in one <path>.
    d = "".join(f"M{x:.1f},{y:.1f}h0" for x, y in map(xy, pts))
    if not d:
        return ""
    return f'<path d="{d}" stroke="{fill}" stroke-width="{size}" stroke-linecap="round" opacity="{opacity}"/>'


@app.function(hide_code=True)
def line(xy, a, b, stroke, width, extra=""):
    (x1, y1), (x2, y2) = xy(a), xy(b)
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" {extra}/>'


@app.function(hide_code=True)
def centroid_marker(xy, c, color, ring=""):
    # A hollow ring, so the points underneath stay visible; `ring` adds a dashed halo.
    x, y = xy(c)
    halo = ""
    if ring:
        halo = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="none" stroke="{ring}" stroke-width="1.5" stroke-dasharray="3 2"/>'
    return (
        halo
        + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="none" stroke="#0f172a" stroke-width="4.5"/>'
        + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="none" stroke="{color}" stroke-width="2.5"/>'
    )


@app.function(hide_code=True)
def step_view(points, centroids, batch=(), assigned=(), weights=None, revived=(), revive_every=0):
    k = len(centroids)
    in_batch = set(batch)
    # `assigned` still holds the previous batch until this batch is assigned.
    fresh = [(x, j) for x, j in assigned if x in in_batch]
    started = weights is not None and max(weights) > 1e-9
    threshold = 0.1 * sum(weights) / k if started else 0
    counts, means = batch_summary(fresh, k)

    def body(xy):
        parts = []
        # Faded background: every point coloured by its nearest centroid right now.
        groups = [[] for _ in range(k)]
        for p in points:
            groups[nearest(p, centroids)].append(p)
        for j in range(k):
            parts.append(dots(xy, groups[j], PALETTE[j], 6, 0.35))
        # The batch: outlined until assigned, then in its cluster's colour.
        waiting = [x for x in batch if x not in dict(fresh)]
        parts.append(dots(xy, waiting, "#0f172a", 8))
        parts.append(dots(xy, waiting, "#f8fafc", 4.5))
        for j in range(k):
            parts.append(dots(xy, [x for x, label in fresh if label == j], PALETTE[j], 8))
        # Where each centroid is being pulled: the mean of its batch points.
        for j in range(k):
            if counts[j]:
                target = means[j]
                tx, ty = xy(target)
                parts.append(line(xy, centroids[j], target, PALETTE[j], 1.5, 'stroke-dasharray="4 3"'))
                parts.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3" fill="#f8fafc" stroke="{PALETTE[j]}" stroke-width="1.5"/>')
        for dead, donor in revived:
            parts.append(line(xy, centroids[dead], centroids[donor], "#f97316", 2))
        revived_now = {j for pair in revived for j in pair}
        for j, c in enumerate(centroids):
            ring = ""
            if j in revived_now:
                ring = "#f97316"
            elif revive_every and started and weights[j] < threshold:
                ring = "#dc2626"
            parts.append(centroid_marker(xy, c, PALETTE[j], ring))
        return "".join(parts)

    return svg_canvas(body)


@app.cell(hide_code=True)
def _():
    k_slider = mo.ui.slider(2, 8, value=6, label="clusters $k$")
    seed_slider = mo.ui.slider(0, 20, value=6, label="seed")
    return k_slider, seed_slider


@app.cell(hide_code=True)
def _(k_slider, seed_slider):
    start = initial_centroids(k_slider.value, seed_slider.value)
    return (start,)


@app.cell(hide_code=True)
def _(k_slider, seed_slider):
    mo.vstack([
        mo.md(r"""
        ## k-means: look at everything, then jump

        All points light up at once, and every centroid jumps to its dashed target.
        """),
        mo.hstack([k_slider, seed_slider], justify="start", gap=2),
    ])
    return


@app.cell(hide_code=True, expand_output=True)
def _(drawn, start):
    lloyd_viewer = mo.ui.anywidget(
        StateViewer(
            e_means,
            step_view,
            args=(drawn, start),
            kwargs={"epochs": 10, "batch_size": len(drawn), "alpha0": 1.0, "floor": 1.0, "revive_every": 0},
            only_changes=True,
            interval_ms=400,
            timeline_func=lambda points, centroids: mse(points, centroids),
            timeline_label="MSE",
            show_code=False,
        )
    )
    lloyd_viewer
    return


@app.cell(hide_code=True)
def _():
    batch_slider = mo.ui.slider(4, 32, value=8, label="batch size $B$")
    # Stops short of 1: at alpha = 1, e-means forgets everything every batch.
    alpha_slider = mo.ui.slider(0.05, 0.9, step=0.05, value=0.4, label=r"step $\alpha_0$")
    return alpha_slider, batch_slider


@app.cell(hide_code=True)
def _(alpha_slider, batch_slider, k_slider, seed_slider):
    mo.vstack([
        mo.md(r"""
        ## e-means: look at a few, then nudge

        Only $B$ points at a time, shared by all centroids. Each centroid moves part of
        the way to its dashed target, and the step $\alpha$ shrinks as the run goes on.

        e-means has one more trick, **revival**: every 5 batches, a cluster whose count has
        faded below a tenth of the average takes over half of a big cluster. A red halo
        marks a starving cluster, an orange line links it to the cluster it takes from.
        """),
        mo.hstack([k_slider, seed_slider, batch_slider, alpha_slider], justify="start", gap=2),
    ])
    return


@app.cell(hide_code=True)
def _(alpha_slider, batch_slider, drawn, seed_slider, start):
    emeans_viewer = mo.ui.anywidget(
        StateViewer(
            e_means,
            step_view,
            args=(drawn, start),
            kwargs={
                "epochs": 2,
                "batch_size": batch_slider.value,
                "alpha0": alpha_slider.value,
                "seed": seed_slider.value,
            },
            only_changes=True,
            interval_ms=250,
            timeline_func=lambda points, centroids: mse(points, centroids),
            timeline_label="MSE",
            show_code=False,
        )
    )
    emeans_viewer
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Does it hold up at scale?

    60,000 Fashion-MNIST images (784 pixels each), $k = 100$, the same algorithm in
    numpy. e-means uses the paper's step $\alpha_0 = 0.4$, at three batch sizes. We
    track the loss against passes over the data *and* against training time.
    It takes about 20 seconds; the first run also downloads about 30 MB.
    """)
    return


@app.function(hide_code=True)
def nearest_np(X, C):
    import numpy as np

    # argmin of |x - c|^2 = |x|^2 - 2 x.c + |c|^2; |x|^2 is the same for every c.
    return np.argmin((C**2).sum(1)[None, :] - 2 * X @ C.T, axis=1)


@app.function(hide_code=True)
def batch_summary_np(X, labels, k):
    import numpy as np

    # Per cluster: how many points it got, and their mean (rows of empty clusters are 0).
    counts = np.bincount(labels, minlength=k).astype(np.float64)
    onehot = np.zeros((len(labels), k), dtype=np.float32)
    onehot[np.arange(len(labels)), labels] = 1
    means = (onehot.T @ X) / np.maximum(counts, 1)[:, None]
    return counts, means


@app.function(hide_code=True)
def mse_np(X, C, chunk=10_000):
    import numpy as np

    total = 0.0
    c2 = (C**2).sum(1)
    for i in range(0, len(X), chunk):
        x = X[i : i + chunk]
        d = (x**2).sum(1)[:, None] - 2 * x @ C.T + c2[None, :]
        total += float(np.maximum(d.min(1), 0).sum())
    return total / len(X)


@app.function(hide_code=True)
def e_means_np(X, centroids, epochs, batch_size, alpha0, floor=0.1, revive_every=5, seed=0, on_epoch=None):
    import numpy as np

    rng = np.random.default_rng(seed)
    k = len(centroids)
    centroids = centroids.astype(np.float32).copy()
    weights = np.full(k, 1e-10)  # no points behind any centroid yet
    per_epoch = len(X) // batch_size
    updates = epochs * per_epoch
    t = 0
    for epoch in range(epochs):
        order = rng.permutation(len(X))
        last_epoch = np.full(len(X), -1)
        for b in range(per_epoch):
            batch = order[b * batch_size : (b + 1) * batch_size]
            t += 1
            alpha = cosine_alpha(t, updates, alpha0, floor)
            labels = nearest_np(X[batch], centroids)  # assign
            counts, means = batch_summary_np(X[batch], labels, k)  # batch_summary
            old, new = (1 - alpha) * weights, alpha * counts  # blend
            got = counts > 0  # a cluster that got no points stays where it is
            centroids[got] = (old[got, None] * centroids[got] + new[got, None] * means[got]) / (old + new)[got, None]
            weights = old + new
            last_epoch[batch] = labels
            if revive_every and t % revive_every == 0:  # revive
                nudge = np.where(np.arange(X.shape[1]) % 2 == 0, 2**-7, -(2**-7))
                for j in np.flatnonzero(weights < 0.1 * weights.mean()):
                    donor = rng.choice(k, p=weights / weights.sum())
                    c = centroids[donor].copy()
                    centroids[j] = c * (1 + nudge)
                    centroids[donor] = c * (1 - nudge)
                    weights[donor] = weights[j] = weights[donor] / 2
        if on_epoch is not None:
            on_epoch(epoch + 1, centroids)
    # finalize: the mean of each cluster's last-epoch points
    seen = last_epoch >= 0
    counts, means = batch_summary_np(X[seen], last_epoch[seen], k)
    centroids[counts > 0] = means[counts > 0]
    return centroids


@app.cell(hide_code=True)
def _():
    run_benchmark = mo.ui.run_button(label="Run the Fashion-MNIST benchmark")
    run_benchmark
    return (run_benchmark,)


@app.cell(hide_code=True)
def _(run_benchmark):
    mo.stop(not run_benchmark.value, mo.md("*Press the button above to run the benchmark.*"))
    import sys
    import time

    import numpy as np
    from sklearn.datasets import fetch_openml

    with mo.status.spinner(title="Loading Fashion-MNIST"):
        pixels, _ = fetch_openml("Fashion-MNIST", version=1, return_X_y=True, as_frame=False, parser="liac-arff")
    # fetch_openml hands back a column-major array; rows must be contiguous, or every
    # batch lookup crawls through memory and dominates the timings.
    images = np.ascontiguousarray(pixels[:60_000] / 255.0, dtype=np.float32)

    K, ALPHA0 = 100, 0.4
    BATCHES = [512, 2048, 8192]
    BUDGETS = [1, 2, 3, 5]
    SEEDS = [0, 1]
    bench_rows = []
    # The two runs the cluster viewer below compares (seed 0).
    viewer_centroids = {}
    # marimo runs cells under a debugger hook (sys.settrace) that taxes every
    # Python call, so switch it off while benchmarking and put it back afterwards.
    previous_trace = sys.gettrace()
    sys.settrace(None)
    nearest_np(images[:2000], images[:K])  # warm up numpy before timing anything
    with mo.status.progress_bar(total=len(SEEDS) * (1 + len(BATCHES) * len(BUDGETS)), title="Benchmarking", remove_on_exit=True) as bar:
        for bench_seed in SEEDS:
            init = images[np.random.default_rng(bench_seed).choice(len(images), K, replace=False)]
            bar.update(increment=0, subtitle=f"seed {bench_seed}: k-means, 25 epochs")

            # Training time only: the clock pauses while we measure the loss after each epoch.
            clock = {"train": 0.0, "since": time.perf_counter()}

            def record(epoch, C, bench_seed=bench_seed, clock=clock):
                clock["train"] += time.perf_counter() - clock["since"]
                bench_rows.append({"run": "k-means", "epochs": epoch, "seed": bench_seed, "seconds": clock["train"], "MSE": mse_np(images, C)})
                clock["since"] = time.perf_counter()

            fitted = e_means_np(images, init, 25, len(images), 1.0, floor=1.0, revive_every=0, on_epoch=record)
            if bench_seed == 0:
                viewer_centroids["k-means, 25 passes"] = fitted
            bar.update()
            # e-means needs its budget up front (the step schedule spans the whole run), so one run per budget.
            for batch_size in BATCHES:
                for budget in BUDGETS:
                    bar.update(increment=0, subtitle=f"seed {bench_seed}: e-means, B = {batch_size}, {budget} epochs")
                    started = time.perf_counter()
                    fitted = e_means_np(images, init, budget, batch_size, ALPHA0, seed=bench_seed)
                    seconds = time.perf_counter() - started
                    bench_rows.append({"run": f"e-means, B = {batch_size}", "epochs": budget, "seed": bench_seed, "seconds": seconds, "MSE": mse_np(images, fitted)})
                    if bench_seed == 0 and batch_size == 512 and budget == 2:
                        viewer_centroids["e-means, 2 passes"] = fitted
                    bar.update()
    sys.settrace(previous_trace)
    return bench_rows, images, viewer_centroids


@app.cell(hide_code=True)
def _(bench_rows):
    # Average over seeds, then divide by k-means after 25 epochs (the paper's yardstick).
    grouped = {}
    for row in bench_rows:
        grouped.setdefault((row["run"], row["epochs"]), []).append(row)
    averaged = [
        {
            "run": run,
            "epochs": epochs,
            "seconds": round(sum(r["seconds"] for r in rows) / len(rows), 3),
            "MSE": sum(r["MSE"] for r in rows) / len(rows),
        }
        for (run, epochs), rows in grouped.items()
    ]
    kmeans_25 = next(r["MSE"] for r in averaged if r["run"] == "k-means" and r["epochs"] == 25)
    for r in averaged:
        r["MSE / k-means@25"] = r["MSE"] / kmeans_25

    colors = alt.Color("run:N", title=None, scale=alt.Scale(
        domain=["k-means", "e-means, B = 512", "e-means, B = 2048", "e-means, B = 8192"],
        range=["#ea580c", "#93c5fd", "#2563eb", "#1e3a8a"],
    ))
    rule = alt.Chart(alt.Data(values=[{"y": 1.0}])).mark_rule(strokeDash=[4, 4], color="#64748b").encode(y="y:Q")

    def bench_panel(x):
        lines = alt.Chart(alt.Data(values=averaged)).mark_line(point=True).encode(
            x=x,
            y=alt.Y("MSE / k-means@25:Q", scale=alt.Scale(zero=False), title="MSE / k-means after 25 passes"),
            color=colors,
            tooltip=["run:N", "epochs:Q", alt.Tooltip("seconds:Q", format=".2f"), alt.Tooltip("MSE / k-means@25:Q", format=".4f")],
        )
        return (lines + rule).properties(width=300, height=260)

    by_pass = bench_panel(alt.X("epochs:Q", title="passes over the data", scale=alt.Scale(type="log", domain=[1, 25]), axis=alt.Axis(values=[1, 2, 3, 5, 10, 25])))
    by_time = bench_panel(alt.X("seconds:Q", title="training time (seconds)", scale=alt.Scale(type="log", nice=False)))
    mo.vstack([
        alt.hconcat(by_pass, by_time),
        mo.accordion({"All numbers (averaged over 2 seeds)": mo.ui.table(averaged, selection=None, page_size=10)}),
    ])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Do the clusters look different?

    Each grid holds one algorithm's 100 centroids, biggest cluster first. Hover a
    centroid to see some of its images. k-means ran 25 passes, e-means 2 passes with
    $B = 512$.
    """)
    return


@app.function(hide_code=True)
def png_strip(rows, side=28):
    # A row of 28x28 images (pixel values 0..1) as one PNG data URL, dark garment on white.
    import base64
    import io

    import numpy as np
    from PIL import Image

    tiles = [255 - np.round(r.reshape(side, side) * 255).astype(np.uint8) for r in rows]
    buffer = io.BytesIO()
    Image.fromarray(np.hstack(tiles)).save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


@app.cell(hide_code=True)
def _(images, viewer_centroids):
    import numpy as _np

    sample_rng = _np.random.default_rng(0)

    def grid_data(title, C):
        # One entry per cluster, biggest first: centroid thumbnail, size, and up to 8 member images.
        labels = _np.concatenate([nearest_np(images[i : i + 10_000], C) for i in range(0, len(images), 10_000)])
        sizes = _np.bincount(labels, minlength=len(C))
        cells = []
        for j in _np.argsort(-sizes):
            members = _np.flatnonzero(labels == j)
            picked = sample_rng.choice(members, min(8, len(members)), replace=False)
            cells.append({
                "thumb": png_strip(C[j : j + 1]),
                "id": int(j),
                "size": int(sizes[j]),
                "sample": png_strip(images[picked]) if len(picked) else "",
            })
        return {"title": title, "cells": cells}

    grid_js = """
    export default {
      render({ model, el }) {
        const { title, cells } = model.get("data");
        el.innerHTML = `<div class="cv"><div class="cv-title">${title}</div><div class="cv-grid"></div><div class="cv-panel">Hover a centroid.</div></div>`;
        const grid = el.querySelector(".cv-grid");
        const panel = el.querySelector(".cv-panel");
        for (const c of cells) {
          const img = document.createElement("img");
          img.src = c.thumb;
          img.className = "cv-thumb";
          img.addEventListener("mouseenter", () => {
            grid.querySelectorAll(".cv-active").forEach((n) => n.classList.remove("cv-active"));
            img.classList.add("cv-active");
            panel.innerHTML = `<div>cluster ${c.id} · ${c.size} images</div>` +
              (c.sample ? `<img class="cv-strip" src="${c.sample}">` : "");
          });
          grid.appendChild(img);
        }
      },
    };
    """
    grid_css = """
    .cv { display: flex; flex-direction: column; gap: 8px; color-scheme: light dark; font-size: 13px; }
    .cv-title { font-weight: 600; }
    .cv-grid { display: grid; grid-template-columns: repeat(10, 28px); gap: 2px; }
    .cv-thumb { width: 28px; height: 28px; image-rendering: pixelated; border-radius: 3px; outline: 1px solid rgba(100, 116, 139, 0.25); cursor: crosshair; }
    .cv-active { outline: 2px solid #2563eb; }
    .cv-panel { display: flex; flex-direction: column; gap: 6px; min-height: 64px; opacity: 0.9; }
    .cv-strip { height: 40px; image-rendering: pixelated; border-radius: 4px; align-self: flex-start; }
    """
    mo.hstack(
        [
            EsmWidget(grid_js, css=grid_css, data=grid_data("k-means, 25 passes", viewer_centroids["k-means, 25 passes"]), width=0, height=420),
            EsmWidget(grid_js, css=grid_css, data=grid_data("e-means, 2 passes", viewer_centroids["e-means, 2 passes"]), width=0, height=420),
        ],
        widths="equal",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Takeaway

    - **2 passes of e-means beat 25 passes of k-means** on Fashion-MNIST, with $B = 512$:
      about a tenth of the training time. At every batch size, e-means is ahead of
      k-means after the same number of passes.
    - **Why:** a pass costs both about the same, but k-means moves the centroids once
      per pass, and e-means with $B = 512$ moves them 117 times. The batch size still
      matters: $B = 2048$ needs 3 passes to catch k-means, and $B = 8192$ (7 moves per
      pass) is still behind after 5.
    - **k-means *is* e-means** with $B$ = all points and $\alpha = 1$. That is how the
      k-means viewer above runs it.
    """)
    return


if __name__ == "__main__":
    app.run()
