# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "altair==6.2.2",
#     "marimo>=0.24.0",
#     "numpy==2.5.2",
#     "polars==1.44.1",
#     "wigglystuff==0.5.32",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Winner's Curse

    There's a bucket of coins on the table. Nobody knows how much it's really
    worth. Everyone squints, makes a **noisy guess**, and bids what they see.

    The catch: the auction is won by whoever guessed *highest* — and the highest
    guess is usually an over-guess. So the winner tends to **overpay**. That's the
    winner's curse.

    Below we simulate it, watch it get worse as more people bid, then find the cure.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import altair as alt
    import polars as pl
    from statistics import NormalDist
    from wigglystuff import HoverSlider

    rng = np.random.default_rng(0)
    return HoverSlider, NormalDist, alt, mo, np, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## One auction

    Set the true value, how fuzzy everyone's guess is, and how many people bid.
    Each dot is one bidder's guess. Bids are in **whole dollars**. The
    winner (highest bid) is highlighted — notice they're almost always sitting
    to the *right* of the true value.
    """)
    return


@app.cell(hide_code=True)
def _(HoverSlider, mo):
    def hslider(start, stop, value, label, step=1):
        return mo.ui.anywidget(
            HoverSlider(start=start, stop=stop, step=step, value=value, label=label, width=320)
        )

    mean = hslider(20, 200, 100, "guess mean (mu, $)")
    sigma = hslider(1, 60, 20, "guess noise (sigma, $)")
    V = hslider(20, 200, 100, "actual value (V, $)")
    n = hslider(2, 60, 8, "number of candidates (n)")

    mo.hstack(
        [
            mo.vstack([mean, sigma]),
            mo.vstack([V, n]),
        ]
    )
    return V, hslider, mean, n, sigma


@app.cell(hide_code=True)
def _(V, alt, mean, mo, n, np, pl, sigma):
    mu_val = float(mean.value["hover_value"])
    sig_val = float(sigma.value["hover_value"])
    Vval = float(V.value["hover_value"])
    n_val = max(2, int(round(n.value["hover_value"])))

    draw_rng = np.random.default_rng(0)
    est = draw_rng.normal(mu_val, sig_val, size=n_val)
    bid = np.clip(np.round(est), 0, None)
    win_idx = int(np.argmax(bid))

    _df = pl.DataFrame(
        {
            "bidder": [f"#{i + 1}" for i in range(n_val)],
            "bid": bid,
            "winner": ["winner" if i == win_idx else "bidder" for i in range(n_val)],
        }
    )

    _pts = (
        alt.Chart(_df)
        .mark_circle(size=140, opacity=0.85)
        .encode(
            x=alt.X("bid:Q", title="bid ($)", scale=alt.Scale(domain=[0, 320], clamp=True)),
            y=alt.Y("winner:N", title="", sort=["winner", "bidder"]),
            color=alt.Color(
                "winner:N",
                title="",
                scale=alt.Scale(domain=["bidder", "winner"], range=["#4C78A8", "#E45756"]),
            ),
            tooltip=["bidder", "bid", "winner"],
        )
    )
    _truth = (
        alt.Chart(pl.DataFrame({"V": [Vval]})).mark_rule(color="#333", size=2).encode(x="V:Q")
    )
    _chart = (_truth + _pts).properties(
        height=160, width="container", title="guesses vs the actual value (black line)"
    )

    mo.vstack(
        [
            mo.md(
                rf"Winner bid **\${int(bid[win_idx])}** for a bucket worth **\${Vval:.0f}** "
                rf"→ overpayment **\${int(bid[win_idx]) - Vval:.0f}**."
            ),
            _chart,
        ]
    )
    return Vval, mu_val, n_val, sig_val


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Repeat it, over and over

    One auction is anecdote. Run **thousands** and the curse shows up as a
    pattern: the distribution of *winning* bids sits stubbornly to the right of
    the actual value. Reuse the sliders above (mean, noise, value, candidates),
    pick how many auctions to run, and hit **run again** to draw a fresh batch.
    """)
    return


@app.cell
def _(np):
    def simulate(mu, sigma, V, n, n_sims, discount=0.0, seed=0):
        r = np.random.default_rng(seed)
        est = r.normal(mu, sigma, size=(n_sims, n))
        bids = np.clip(np.round(est - discount), 0, None)
        winning = bids.max(axis=1)
        overpay = winning - V
        return winning, overpay

    return (simulate,)


@app.cell
def _(NormalDist):
    def expected_top_gap(n):
        """a_n = E[max of n standard normals], via Blom's approximation
        a_n ~= Phi^{-1}((n - 0.375) / (n + 0.25))."""
        return NormalDist().inv_cdf((n - 0.375) / (n + 0.25))

    def expected_max(mu, sigma, n):
        """Expected largest of n guesses drawn from N(mu, sigma^2): mu + sigma * a_n."""
        return mu + sigma * expected_top_gap(n)

    def bid_discount(believed_sigma, n):
        """Bid this far below your estimate: believed noise x expected top gap."""
        return believed_sigma * expected_top_gap(n)

    return bid_discount, expected_top_gap


@app.cell
def _(hslider, mo):
    n_sims = hslider(200, 8000, 3000, "number of auctions", step=200)
    run_btn = mo.ui.button(label="🎲 run again", value=0, on_click=lambda v: v + 1)
    mo.hstack([n_sims, run_btn])
    return n_sims, run_btn


@app.cell
def _(Vval, alt, mo, mu_val, n_sims, n_val, pl, run_btn, sig_val, simulate):
    winning, overpay = simulate(
        mu_val,
        sig_val,
        Vval,
        n_val,
        int(n_sims.value["hover_value"]),
        discount=0.0,
        seed=run_btn.value,
    )

    _df = pl.DataFrame({"winning_bid": winning})
    _bars = (
        alt.Chart(_df)
        .mark_bar(opacity=0.85, color="#4C78A8")
        .encode(
            x=alt.X(
                "winning_bid:Q",
                bin=alt.Bin(maxbins=50),
                title="winning bid ($)",
                scale=alt.Scale(domain=[0, 320], clamp=True),
            ),
            y=alt.Y("count()", title="auctions"),
        )
    )
    _truth = (
        alt.Chart(pl.DataFrame({"V": [Vval]})).mark_rule(color="#333", size=2).encode(x="V:Q")
    )
    _chart = (_bars + _truth).properties(
        height=260,
        width="container",
        title="distribution of winning bids (actual value = black line)",
    )

    mo.vstack(
        [
            mo.md(
                rf"Across **{int(n_sims.value['hover_value']):,}** auctions the winner overpaid on average by "
                rf"**\${overpay.mean():.1f}** "
                rf"(won below value only **{(overpay < 0).mean() * 100:.0f}%** of the time)."
            ),
            _chart,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## More competition, worse curse

    Hold the bucket fixed and vary how many people bid. With more candidates, the
    highest guess is drawn from further out in the tail — so the winner overpays
    by more. The curse *grows* with the size of the crowd.
    """)
    return


@app.cell
def _(Vval, alt, mu_val, n_sims, np, pl, run_btn, sig_val, simulate):
    _n_grid = np.arange(2, 31)
    _op = [
        simulate(
            mu_val,
            sig_val,
            Vval,
            int(k),
            int(n_sims.value["hover_value"]),
            discount=0.0,
            seed=run_btn.value,
        )[1].mean()
        for k in _n_grid
    ]
    _df = pl.DataFrame({"n": _n_grid, "overpay": _op})

    _line = (
        alt.Chart(_df)
        .mark_line(color="#E45756")
        .encode(
            x=alt.X("n:Q", title="number of candidates"),
            y=alt.Y("overpay:Q", title="mean overpayment ($)"),
            tooltip=["n", alt.Tooltip("overpay:Q", format=".1f")],
        )
    )
    _zero = alt.Chart(pl.DataFrame({"y": [0]})).mark_rule(color="#333").encode(y="y:Q")

    (_zero + _line).properties(
        height=280, width="container", title="the more bidders, the worse the curse"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The cure: discount your bid

    Don't pull a number out of thin air. If you win, you almost certainly held the
    *highest* of the $n$ guesses. For guesses drawn as $x_i \sim N(\mu, \sigma^2)$,
    the expected largest one is

    $$\mathbb{E}\!\left[\max_i x_i\right] = \mu + \sigma\, a_n,
      \qquad a_n \approx \Phi^{-1}\!\left(\frac{n - 0.375}{n + 0.25}\right),$$

    so the top guess sits about $\sigma\, a_n$ above the truth, and $a_n$ grows with
    the crowd. **Discount** your bid by exactly that — your believed noise times the
    top-gap $a_n$. Get your belief right and the curse vanishes at every crowd size;
    underestimate the noise and it bites again.

    The approximation for $a_n$ is
    [Blom's formula for normal order statistics](https://en.wikipedia.org/wiki/Order_statistic#Approximating_the_moments).
    """)
    return


@app.cell
def _(hslider):
    belief_sigma = hslider(1, 60, 20, "our believed noise (sigma-hat, $)")
    belief_sigma
    return (belief_sigma,)


@app.cell
def _(
    Vval,
    alt,
    belief_sigma,
    bid_discount,
    expected_top_gap,
    mo,
    mu_val,
    n_sims,
    n_val,
    np,
    pl,
    run_btn,
    sig_val,
    simulate,
):
    sighat = float(belief_sigma.value["hover_value"])
    _n_grid = np.arange(2, 31)
    _rows = []
    for k in _n_grid:
        _d = bid_discount(sighat, int(k))
        for _lbl, _dd in [("naive (no discount)", 0.0), ("discounted by the rule", _d)]:
            _op = simulate(
                mu_val,
                sig_val,
                Vval,
                int(k),
                int(n_sims.value["hover_value"]),
                discount=_dd,
                seed=run_btn.value,
            )[1].mean()
            _rows.append({"n": int(k), "overpay": _op, "strategy": _lbl})
    _df = pl.DataFrame(_rows)

    _lines = (
        alt.Chart(_df)
        .mark_line()
        .encode(
            x=alt.X("n:Q", title="number of candidates"),
            y=alt.Y("overpay:Q", title="mean overpayment ($)"),
            color=alt.Color(
                "strategy:N",
                title="",
                scale=alt.Scale(
                    domain=["naive (no discount)", "discounted by the rule"],
                    range=["#E45756", "#4C78A8"],
                ),
            ),
            tooltip=["n", "strategy", alt.Tooltip("overpay:Q", format=".1f")],
        )
    )
    _zero = alt.Chart(pl.DataFrame({"y": [0]})).mark_rule(color="#333").encode(y="y:Q")

    _disc_now = bid_discount(sighat, n_val)
    _win, _op_now = simulate(
        mu_val,
        sig_val,
        Vval,
        n_val,
        int(n_sims.value["hover_value"]),
        discount=_disc_now,
        seed=run_btn.value,
    )
    _profit = -_op_now.mean()

    mo.vstack(
        [
            mo.md(
                rf"At **{n_val}** candidates the rule discounts by **\${_disc_now:.1f}** "
                rf"(= believed noise \${sighat:.0f} x top-gap {expected_top_gap(n_val):.2f}), "
                rf"turning the average result into a **\${_profit:+.1f}** outcome for the winner."
            ),
            (_zero + _lines).properties(
                height=280,
                width="container",
                title="discounting by the rule flattens the curse across crowd sizes",
            ),
        ]
    )
    return (sighat,)


@app.cell
def _(
    Vval,
    alt,
    bid_discount,
    mu_val,
    n_sims,
    n_val,
    np,
    pl,
    run_btn,
    sig_val,
    sighat,
    simulate,
):
    _disc = bid_discount(sighat, n_val)
    _wn = simulate(
        mu_val,
        sig_val,
        Vval,
        n_val,
        int(n_sims.value["hover_value"]),
        discount=0.0,
        seed=run_btn.value,
    )[0]
    _wd = simulate(
        mu_val,
        sig_val,
        Vval,
        n_val,
        int(n_sims.value["hover_value"]),
        discount=_disc,
        seed=run_btn.value,
    )[0]

    _df = pl.DataFrame(
        {
            "winning_bid": np.concatenate([_wn, _wd]),
            "strategy": (["naive (no discount)"] * len(_wn))
            + (["discounted by the rule"] * len(_wd)),
        }
    )

    _bars = (
        alt.Chart(_df)
        .mark_bar(opacity=0.55)
        .encode(
            x=alt.X(
                "winning_bid:Q",
                bin=alt.Bin(maxbins=50),
                title="winning bid ($)",
                scale=alt.Scale(domain=[0, 320], clamp=True),
            ),
            y=alt.Y("count()", title="auctions", stack=None),
            color=alt.Color(
                "strategy:N",
                title="",
                scale=alt.Scale(
                    domain=["naive (no discount)", "discounted by the rule"],
                    range=["#E45756", "#4C78A8"],
                ),
            ),
        )
    )
    _truth = (
        alt.Chart(pl.DataFrame({"V": [Vval]})).mark_rule(color="#333", size=2).encode(x="V:Q")
    )

    (_bars + _truth).properties(
        height=260,
        width="container",
        title=f"winning bids at n={n_val}: discounting slides the mass onto the actual value",
    )
    return


if __name__ == "__main__":
    app.run()
