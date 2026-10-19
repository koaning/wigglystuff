# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.35",
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

    from wigglystuff import StateViewer

    return StateViewer, mo


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


if __name__ == "__main__":
    app.run()
