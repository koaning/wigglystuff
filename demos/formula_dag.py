# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "wigglystuff==0.5.37",
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

    from wigglystuff import FormulaDAG

    return FormulaDAG, mo


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
                "vol": r"\sigma_T = \tangle{sigma}\sqrt{\tangle{T}}",
                "disc": r"D = \note{discount}{e^{-\tangle{r}\tangle{T}}}",
                "d1": r"\note{d1}{d_1} = \frac{\note{moneyness}{\ln(\tangle{S}/\tangle{K})} + (\tangle{r} + \tfrac{1}{2}\tangle{sigma}^2)\tangle{T}}{\use{vol}}",
                "d2": r"\note{d2}{d_2} = \use{d1} - \use{vol}",
                "call": {
                    "tex": r"C = \tangle{S}\,N(\use{d1}) - \tangle{K}\,\use{disc}\,\note{exercise}{N(\use{d2})}",
                    "label": "call price",
                },
                "put": {
                    "tex": r"P = \use{call} - \tangle{S} + \tangle{K}\,\use{disc}",
                    "label": "put (via parity)",
                },
                "delta": {
                    "tex": r"\Delta_C = N(\use{d1})",
                    "label": "call delta",
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
    # The widget only draws the formulas; the numbers come from Python. `values`
    # follows a drag live, while `committed_values` keeps the numbers from before
    # the drag until you let go, so mid-drag we can show what changed.
    import math

    def _N(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _price(v):
        vol = v["sigma"] * math.sqrt(v["T"])
        disc = math.exp(-v["r"] * v["T"])
        d1 = (math.log(v["S"] / v["K"]) + (v["r"] + v["sigma"] ** 2 / 2) * v["T"]) / vol
        d2 = d1 - vol
        call = v["S"] * _N(d1) - v["K"] * disc * _N(d2)
        return {"call": call, "put": call - v["S"] + v["K"] * disc, "delta": _N(d1)}

    _now = _price(bs.values)
    _was = _price(bs.committed_values)

    def _show(key, digits):
        text = f"**{key}** {_now[key]:.{digits}f}"
        if bs.dragging and abs(_now[key] - _was[key]) > 10 ** -digits / 2:
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


if __name__ == "__main__":
    app.run()
