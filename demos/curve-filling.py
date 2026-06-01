# /// script
# dependencies = [
#     "altair==6.1.0",
#     "marimo",
#     "matplotlib==3.10.9",
#     "numpy==2.4.6",
#     "pandas==3.0.3",
#     "wigglystuff==0.5.7",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="columns", sql_output="polars")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md("""
    # Exploring in circles

    A **space-filling curve** visits every cell of a 2D grid in a single 1D
    order, so that points nearby on the curve tend to be nearby in the plane.
    Different curves make different trade-offs in how well they preserve that
    locality — and where they "teleport" across the plane.

    This notebook lets you compare four of them:

    - **Morton (x, y)** — interleave the bits of x and y into one integer (the
      classic "Z"-order curve).
    - **Morton (y, x)** — the same trick with the interleave order swapped.
    - **Hilbert** — visits every cell with *no* long jumps: consecutive ranks
      are always in adjacent cells.
    - **Moore** — a closed-loop Hilbert variant whose start and end cells are
      adjacent, so the order wraps around like a ring.

    Pick a curve from the dropdown, then drag the **circular slider** to select
    a window of ranks along the curve and see which 2D points it highlights. The
    circular control has no seam — drag past the top and the range wraps around,
    matching the looping nature of the Moore curve.
    """)
    return (mo,)


@app.cell(hide_code=True)
def _():
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from wigglystuff import CircularRangeSlider

    return CircularRangeSlider, np, pd, plt


@app.cell(hide_code=True)
def _(np):
    rng = np.random.default_rng(0)
    N = 1500
    BITS = 10  # quantization resolution per axis: 2**10 = 1024 bins

    xs = rng.random(N)
    ys = rng.random(N)
    return BITS, N, xs, ys


@app.cell(hide_code=True)
def _(BITS, N, np, pd, xs, ys):
    def morton_code(x_int, y_int, bits):
        """Interleave bits of x_int and y_int (each in [0, 2**bits))."""
        code = np.zeros_like(x_int, dtype=np.int64)
        for i in range(bits):
            code |= ((x_int >> i) & 1) << (2 * i)
            code |= ((y_int >> i) & 1) << (2 * i + 1)
        return code


    def as_bits(values, width):
        return [format(int(v), f"0{width}b") for v in values]


    x_int = np.minimum((xs * (1 << BITS)).astype(np.int64), (1 << BITS) - 1)
    y_int = np.minimum((ys * (1 << BITS)).astype(np.int64), (1 << BITS) - 1)
    codes = morton_code(x_int, y_int, BITS)

    order = np.argsort(codes)
    df = pd.DataFrame(
        {
            "rank": np.arange(N),
            "x": xs[order],
            "y": ys[order],
            "x_bits": as_bits(x_int[order], BITS),
            "y_bits": as_bits(y_int[order], BITS),
            "code": codes[order],
            "code_bits": as_bits(codes[order], 2 * BITS),
        }
    )
    return as_bits, df, morton_code, x_int, y_int


@app.cell(hide_code=True)
def _(mo):
    curve_pick = mo.ui.dropdown(
        options={
            "Morton (x, y)": "xy",
            "Morton (y, x)": "yx",
            "Hilbert": "h",
            "Moore (closed loop)": "m",
        },
        value="Morton (x, y)",
        label="Curve",
    )
    curve_pick
    return (curve_pick,)


@app.cell(hide_code=True)
def _(CircularRangeSlider, N, mo):
    circular_mpl = mo.ui.anywidget(
        CircularRangeSlider(
            start=0,
            stop=N - 1,
            step=1,
            value=(0, N // 4),
            size=240,
            color="#e45756",
            label="Rank window",
        )
    )
    return (circular_mpl,)


@app.cell(hide_code=True)
def _(circular_mpl, curve_pick, df, df_h, df_m, df_yx, mo, pd, plt):
    # matplotlib view — drag the slider to pick a window of ranks along the curve.
    _dfs = {"xy": df, "yx": df_yx, "h": df_h, "m": df_m}
    _colors = {"xy": "#e45756", "yx": "#4c78a8", "h": "#54a24b", "m": "#b279a2"}
    _titles = {"xy": "Morton (x, y)", "yx": "Morton (y, x)", "h": "Hilbert", "m": "Moore"}

    _key = curve_pick.value
    _dfm = _dfs[_key]
    _c = _colors[_key]

    # Raw (low, high) from the circular slider. low > high means the arc wraps
    # across the seam, i.e. "from low, through the top, round to high".
    _lo, _hi = (int(v) for v in circular_mpl.value["value"])
    _wrap = _lo > _hi

    if not _wrap:
        _segments = [_dfm[(_dfm["rank"] >= _lo) & (_dfm["rank"] <= _hi)]]
    elif _key == "m":
        # Moore is a closed loop: the seam edge (rank N-1 -> 0) is real, so the
        # wrapped selection is one continuous path.
        _segments = [
            pd.concat(
                [_dfm[_dfm["rank"] >= _lo], _dfm[_dfm["rank"] <= _hi]],
                ignore_index=True,
            )
        ]
    else:
        # Open curves: a wrapped selection is two disjoint pieces of the path —
        # don't draw a connector across the seam.
        _segments = [_dfm[_dfm["rank"] >= _lo], _dfm[_dfm["rank"] <= _hi]]

    _selm = pd.concat(_segments, ignore_index=True)

    # recolor the slider to match the highlight color of the current curve
    circular_mpl.widget.color = _c

    _fig, _ax = plt.subplots(figsize=(5.2, 5.2))
    _ax.plot(_dfm["x"], _dfm["y"], color="#bbbbbb", lw=1, zorder=1)
    _ax.scatter(_dfm["x"], _dfm["y"], s=16, color="#cccccc", zorder=2)
    for _seg in _segments:
        _ax.plot(_seg["x"], _seg["y"], color=_c, lw=2, zorder=3)
    _ax.scatter(_selm["x"], _selm["y"], s=42, color=_c, zorder=4)
    _ax.set(
        xlim=(0, 1),
        ylim=(0, 1),
        title=f"{_titles[_key]} — ranks [{_lo}, {_hi}]" + (" (wrapping)" if _wrap else ""),
    )
    _ax.set_aspect("equal")
    mo.hstack([circular_mpl, _ax], align="center", justify="start")
    return


@app.cell(hide_code=True)
def _(BITS, N, as_bits, morton_code, np, pd, x_int, xs, y_int, ys):
    codes_yx = morton_code(y_int, x_int, BITS)  # swapped order
    order_yx = np.argsort(codes_yx)
    df_yx = pd.DataFrame(
        {
            "rank": np.arange(N),
            "x": xs[order_yx],
            "y": ys[order_yx],
            "x_bits": as_bits(x_int[order_yx], BITS),
            "y_bits": as_bits(y_int[order_yx], BITS),
            "code": codes_yx[order_yx],
            "code_bits": as_bits(codes_yx[order_yx], 2 * BITS),
        }
    )
    return (df_yx,)


@app.cell(hide_code=True)
def _(BITS, N, as_bits, np, pd, x_int, xs, y_int, ys):
    def hilbert_d(x, y, bits):
        """Map 2D integer coords to Hilbert curve index. Grid side = 2**bits."""
        n = 1 << bits
        x = x.copy()
        y = y.copy()
        d = np.zeros_like(x, dtype=np.int64)
        s = n // 2
        while s > 0:
            rx = ((x & s) > 0).astype(np.int64)
            ry = ((y & s) > 0).astype(np.int64)
            d += s * s * ((3 * rx) ^ ry)
            # rotate quadrant when ry == 0
            flip = ry == 0
            # if rx == 1 and ry == 0: reflect within the sub-square
            refl = flip & (rx == 1)
            x = np.where(refl, s - 1 - x, x)
            y = np.where(refl, s - 1 - y, y)
            # if ry == 0: swap x and y
            x_new = np.where(flip, y, x)
            y_new = np.where(flip, x, y)
            x, y = x_new, y_new
            s //= 2
        return d


    hcodes = hilbert_d(x_int, y_int, BITS)
    order_h = np.argsort(hcodes)
    df_h = pd.DataFrame(
        {
            "rank": np.arange(N),
            "x": xs[order_h],
            "y": ys[order_h],
            "x_bits": as_bits(x_int[order_h], BITS),
            "y_bits": as_bits(y_int[order_h], BITS),
            "hilbert": hcodes[order_h],
        }
    )
    return df_h, hilbert_d


@app.cell(hide_code=True)
def _(BITS, N, hilbert_d, np, pd, x_int, xs, y_int, ys):
    def moore_d(x, y, bits):
        """Moore curve index. Grid side = 2**bits, bits >= 1."""
        half = 1 << (bits - 1)
        qsize = half * half

        qx = (x >= half).astype(np.int64)
        qy = (y >= half).astype(np.int64)
        lx = x - qx * half
        ly = y - qy * half

        # quadrant traversal order: BL=0, TL=1, TR=2, BR=3
        quad_order = np.where(
            qy == 0,
            np.where(qx == 0, 0, 3),
            np.where(qx == 0, 1, 2),
        )

        s = half
        hx = np.where(qx == 0, ly, s - 1 - ly)
        hy = np.where(qx == 0, s - 1 - lx, lx)

        sub_d = hilbert_d(hx, hy, bits - 1)
        return quad_order * qsize + sub_d


    mcodes = moore_d(x_int, y_int, BITS)
    order_m = np.argsort(mcodes)
    df_m = pd.DataFrame(
        {
            "rank": np.arange(N),
            "x": xs[order_m],
            "y": ys[order_m],
            "moore": mcodes[order_m],
        }
    )
    return (df_m,)


if __name__ == "__main__":
    app.run()
