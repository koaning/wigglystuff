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
    and every formula showing it follows. `\note{name}{...}` adds the
    plain-language notes. Click a formula to select it.
    """)
    return


@app.cell(expand_output=True)
def _(FormulaDAG, mo):
    def _number(value, lo, hi, step, symbol, digits=2):
        return {
            "value": value,
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
                "d1": r"d_1 = \frac{\note{moneyness}{\ln(\tangle{S}/\tangle{K})} + (\tangle{r} + \tfrac{1}{2}\tangle{sigma}^2)\tangle{T}}{\use{vol}}",
                "d2": r"d_2 = \use{d1} - \use{vol}",
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
                "S": _number(100, 50, 150, 1, "S", digits=0),
                "K": _number(100, 50, 150, 1, "K", digits=0),
                "r": _number(0.05, 0, 0.2, 0.005, "r", digits=3),
                "sigma": _number(0.2, 0.05, 1, 0.01, r"\sigma"),
                "T": _number(1, 0.1, 5, 0.1, "T", digits=1),
            },
            notes={
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
    # The widget only draws the formulas; the numbers come from Python, reading
    # the live `values` that the drag updates.
    import math

    def _N(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    _v = bs.values
    _vol = _v["sigma"] * math.sqrt(_v["T"])
    _disc = math.exp(-_v["r"] * _v["T"])
    _d1 = (math.log(_v["S"] / _v["K"]) + (_v["r"] + _v["sigma"] ** 2 / 2) * _v["T"]) / _vol
    _d2 = _d1 - _vol
    _call = _v["S"] * _N(_d1) - _v["K"] * _disc * _N(_d2)
    _put = _call - _v["S"] + _v["K"] * _disc
    mo.md(
        f"**call** {_call:.2f} · **put** {_put:.2f} · **delta** {_N(_d1):.3f} "
        f"· d₁ {_d1:.3f} · d₂ {_d2:.3f}"
    )
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
