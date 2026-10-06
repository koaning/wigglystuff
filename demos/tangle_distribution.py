# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "altair==6.0.0",
#     "marimo",
#     "numpy==2.4.1",
#     "pandas==2.3.3",
#     "wigglystuff==0.5.33",
# ]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd

    from wigglystuff import TangleDistribution, TangleSlider

    return TangleDistribution, TangleSlider, alt, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # TangleDistribution

    Sometimes a single number is too confident. `TangleDistribution` is a
    [Tangle](https://worrydream.com/Tangle/)-style inline control that holds a whole
    distribution. **Drag left/right** to change one parameter and **up/down** to
    change the other. A small chart pops up while you drag: the dashed curve is
    where you started and the solid curve is where you are now.

    The text shows the distribution's mean ± standard deviation by default, and
    you can change it with `template` (see further down). Fourteen families are
    supported (`TangleDistribution.distributions`): nine continuous ones and five
    discrete ones. Their names and parameters follow `scipy.stats`, but the maths
    is built in, so `cdf`, `ppf`, `pdf`/`pmf` and `sample` work without scipy.
    Hold **Shift** for coarser steps or **Alt/Option** for finer ones.
    """)
    return


@app.cell
def _(alt, mo, np, pd):
    def inspect(w):
        """The committed distribution (grey) and, mid-drag, the live one (blue), next to what Python sees."""
        # Span the bulk of both distributions, plus a little room for edges like uniform's.
        _both = np.concatenate([w.sample(2000, seed=0), w.sample(2000, seed=0, live=True)])
        lo, hi = np.quantile(_both, [0.001, 0.999])
        if w.discrete:
            x = np.arange(np.floor(lo), np.ceil(hi) + 1)
            density, mark = w.pmf, "mark_bar"
        else:
            pad = 0.05 * (hi - lo)
            x = np.linspace(lo - pad, hi + pad, 400)
            density, mark = w.pdf, "mark_line"

        frames = [pd.DataFrame({"x": x, "density": density(x), "version": "committed"})]
        if w.dragging:
            frames.append(pd.DataFrame({"x": x, "density": density(x, live=True), "version": "live"}))
        chart = (
            getattr(alt.Chart(pd.concat(frames)), mark)(opacity=0.7)
            .encode(
                x=alt.X("x:Q").title(None),
                y=alt.Y("density:Q").stack(None).title(None),
                color=alt.Color("version:N")
                .scale(domain=["committed", "live"], range=["#8c959f", "#0066cc"])
                .legend(orient="top", title=None),
            )
            .properties(width=360, height=140)
        )
        state = mo.md(f"""
    | | |
    | --- | --- |
    | `params` | `{w.params}` |
    | `live_params` | `{w.live_params}` |
    | `dragging` | `{w.dragging}` |
    | `mean ± sd` | `{w.mean:.3f} ± {w.sd:.3f}` |
    | 80% interval | `ppf(0.1) = {w.ppf(0.1):.3f}` to `ppf(0.9) = {w.ppf(0.9):.3f}` |
    | `template_fields` | `{w.template_fields}` |
    """)
        return mo.hstack([chart, state], justify="start", align="center", gap=2)

    return (inspect,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Each family below gets a widget in a sentence and, right underneath, the same
    distribution drawn from Python with `widget.pdf(x)` (or `widget.pmf(k)` for
    the discrete families), next to what Python sees.
    `params` only changes when you let go; `live_params` follows the pointer while
    `dragging` is `True`, so mid-drag the chart shows the committed curve (grey)
    and the live one (blue) together.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Continuous families

    These take any value in a range, so they have a density: `widget.pdf(x)`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Normal: `norm`

    The symmetric bell curve. **↔** moves `loc` (the mean) and **↕** changes
    `scale` (the standard deviation), so for this family the text is exactly
    `loc ± scale`.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    norm = mo.ui.anywidget(TangleDistribution("norm", params={"loc": 18, "scale": 3}, steps={"scale": 0.1}, template="{mean} ± {sd} °C"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"Tomorrow it will be {norm} outside.")
    return (norm,)


@app.cell(hide_code=True)
def _(inspect, norm):
    inspect(norm)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Log-normal: `lognorm`

    Positive and right-skewed, for things that can't go below zero and
    occasionally run long. **↔** moves `scale`, which is the median, and **↕**
    changes `s`, the spread in log space: a bigger `s` means a longer right tail.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    lognorm = mo.ui.anywidget(TangleDistribution("lognorm", params={"scale": 120, "s": 0.5}, template="{mean:.0f} ± {sd:.0f} ms"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"An API call takes {lognorm}.")
    return (lognorm,)


@app.cell(hide_code=True)
def _(inspect, lognorm):
    inspect(lognorm)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Gamma: `gamma`

    Also positive and right-skewed, with a lighter tail than `lognorm`; a
    classic for waiting times. **↔** stretches the whole curve with `scale` and
    **↕** changes the shape `a`: at `a = 1` it is an exponential, and larger
    values look more and more like a bell.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    gamma = mo.ui.anywidget(TangleDistribution("gamma", params={"a": 2, "scale": 3}, template="{mean} ± {sd} minutes"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"The next bus comes in {gamma}.")
    return (gamma,)


@app.cell(hide_code=True)
def _(gamma, inspect):
    inspect(gamma)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Exponential: `expon`

    The time until the next event when events happen at a steady rate, like
    customers walking into a shop. One parameter, so only **↔** does anything:
    `scale` is the average wait (and also the sd). It is gamma with `a = 1`.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    expon = mo.ui.anywidget(TangleDistribution("expon", params={"scale": 4}, template="every {scale} minutes"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"On average, a customer walks in {expon}.")
    return (expon,)


@app.cell(hide_code=True)
def _(expon, inspect):
    inspect(expon)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Weibull: `weibull_min`

    Time until something breaks. **↔** stretches it with `scale` and **↕**
    changes the shape `c`: below 1 most failures happen early, at 1 it is an
    exponential, and above 1 things wear out with age.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    weibull_min = mo.ui.anywidget(TangleDistribution("weibull_min", params={"scale": 6, "c": 2}, template="{mean:.1f} ± {sd:.1f} years"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"A hard drive lasts {weibull_min}.")
    return (weibull_min,)


@app.cell(hide_code=True)
def _(inspect, weibull_min):
    inspect(weibull_min)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Uniform: `uniform`

    Every value in a range is equally likely. **↔** slides the range with `loc`
    (its left edge) and **↕** widens it with `scale` (its width).
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    uniform = mo.ui.anywidget(TangleDistribution("uniform", params={"loc": 40, "scale": 20}))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"The delivery arrives {uniform} minutes after noon.")
    return (uniform,)


@app.cell(hide_code=True)
def _(inspect, uniform):
    inspect(uniform)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Laplace: `laplace`

    Like the normal, but with a sharper peak and heavier tails: mostly small
    changes with the odd big jump. **↔** moves `loc` and **↕** changes `scale`
    (the sd is `√2 · scale`).
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    laplace = mo.ui.anywidget(TangleDistribution("laplace", params={"loc": 0, "scale": 1}, template="{mean:.1f} ± {sd:.1f}%"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"Tomorrow the stock moves {laplace}.")
    return (laplace,)


@app.cell(hide_code=True)
def _(inspect, laplace):
    inspect(laplace)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Logistic: `logistic`

    Bell-shaped with slightly heavier tails than the normal. Its cdf is the
    S-shaped logistic curve, which is why it turns up in logistic regression and
    Elo ratings. **↔** moves `loc` and **↕** changes `scale` (the sd is
    `π · scale / √3`).
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    logistic = mo.ui.anywidget(TangleDistribution("logistic", params={"loc": 1500, "scale": 100}, steps={"loc": 10, "scale": 5}, template="{mean:.0f} ± {sd:.0f}"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"The player's true chess rating is {logistic}.")
    return (logistic,)


@app.cell(hide_code=True)
def _(inspect, logistic):
    inspect(logistic)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Beta: `beta`

    Lives between 0 and 1, so it suits rates and proportions. **↔** raises `a`,
    which pulls the mass towards 1, and **↕** raises `b`, which pulls it towards 0.
    When `a = b` the curve is symmetric, and larger values make it narrower.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    beta = mo.ui.anywidget(TangleDistribution("beta", params={"a": 2, "b": 5}))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"The click-through rate is {beta}.")
    return (beta,)


@app.cell(hide_code=True)
def _(beta, inspect):
    inspect(beta)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Discrete families

    These only take whole numbers, so they have a probability mass function,
    `widget.pmf(k)`, and the preview draws bars.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Poisson: `poisson`

    Counts of independent events in a fixed window: emails per hour, typos per
    page. It has a single parameter, so only **↔** does anything: it moves `mu`,
    which is both the mean and the variance. Being discrete, it uses `pmf(k)`
    rather than `pdf(x)`, and the preview shows bars.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    poisson = mo.ui.anywidget(TangleDistribution("poisson", params={"mu": 4}, template="{mean} ± {sd} emails"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"This hour I expect {poisson}.")
    return (poisson,)


@app.cell(hide_code=True)
def _(inspect, poisson):
    inspect(poisson)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Binomial: `binom`

    The number of successes in `n` independent tries that each succeed with
    probability `p`. **↔** moves `p` and **↕** changes `n`, which only takes
    whole numbers (Alt's fine mode doesn't apply to it).
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    binom = mo.ui.anywidget(TangleDistribution("binom", params={"p": 0.3, "n": 20}, template="{mean:.1f} of {n} visitors (p = {p})"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"Of today's visitors, I expect {binom} to sign up.")
    return (binom,)


@app.cell(hide_code=True)
def _(binom, inspect):
    inspect(binom)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Negative binomial: `nbinom`

    Counts that vary more than a Poisson allows, like support tickets per day.
    In scipy's definition it counts the failures before the `n`-th success, where
    each try succeeds with probability `p`. **↔** moves `p` and **↕** changes
    `n`, which doesn't have to be a whole number.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    nbinom = mo.ui.anywidget(TangleDistribution("nbinom", params={"p": 0.3, "n": 5}, template="{mean:.1f} ± {sd:.1f} tickets"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"Tomorrow we get {nbinom}.")
    return (nbinom,)


@app.cell(hide_code=True)
def _(inspect, nbinom):
    inspect(nbinom)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Geometric: `geom`

    The number of tries until the first success, counting the success itself
    (so it starts at 1, as in scipy). One parameter: **↔** moves `p`, the chance
    each try succeeds, so dragging right means fewer tries.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    geom = mo.ui.anywidget(TangleDistribution("geom", params={"p": 0.25}, template="{mean:.1f} ± {sd:.1f} laps"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"Finding a parking spot takes {geom} around the block.")
    return (geom,)


@app.cell(hide_code=True)
def _(geom, inspect):
    inspect(geom)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Random integer: `randint`

    Every whole number from `low` up to, but not including, `high` is equally
    likely (scipy excludes `high` too). **↔** moves `low` and **↕** moves
    `high`; dragging `high` down pushes `low` along so the range never empties.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    randint = mo.ui.anywidget(TangleDistribution("randint", params={"low": 1, "high": 7}, template="{low} up to {high} (excluding {high})"))
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"A die roll is any whole number from {randint}.")
    return (randint,)


@app.cell(hide_code=True)
def _(inspect, randint):
    inspect(randint)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Customising the text

    `template` controls the inline text. The placeholders are the keys of
    `params` (the family's scipy parameter names) plus the computed `mean` and
    `sd`. `widget.template_fields` lists them, and every family's readout above
    shows them too.

    Add `:.Nf` to pick the decimals for a placeholder, e.g. `{mean:.0f}`; anything
    outside the braces is plain text. A placeholder the family doesn't have raises
    a `ValueError` that lists the valid ones.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    budget = mo.ui.anywidget(TangleDistribution(
        "norm", params={"loc": 1200, "scale": 150}, steps={"loc": 10, "scale": 10},
        template="${mean:.0f} ± ${sd:.0f}",
    ))
    commute = mo.ui.anywidget(TangleDistribution(
        "lognorm", params={"scale": 25, "s": 0.3},
        template="{scale:.0f} minutes (median, s = {s})",
    ))
    wait = mo.ui.anywidget(TangleDistribution(
        "gamma", params={"a": 2, "scale": 3},
        template="about {mean:.0f} minutes, give or take {sd:.0f}",
    ))
    rate = mo.ui.anywidget(TangleDistribution(
        "beta", params={"a": 2, "b": 5},
        template="{mean:.2f} (a = {a}, b = {b})",
    ))
    mo.md(f"""
    - The project costs {budget}.
    - My commute takes {commute}.
    - The queue at the bakery is {wait}.
    - The conversion rate is {rate}.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Example: will we ship on time?

    Task durations can't be negative and tend to run long, which makes `lognorm`
    a better fit than `norm`. Its `scale` is the median duration and `s` sets how
    far it can run over. Drag the estimates below and watch the chance of missing
    the deadline update live, with the *before* (grey) next to the *now* (blue).
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, TangleSlider, mo):
    design = mo.ui.anywidget(
        TangleDistribution("lognorm", params={"scale": 5, "s": 0.2}, steps={"scale": 0.1}, template="{mean} ± {sd} days")
    )
    build = mo.ui.anywidget(
        TangleDistribution("lognorm", params={"scale": 10, "s": 0.4}, steps={"scale": 0.1}, template="{mean} ± {sd} days")
    )
    deadline = mo.ui.anywidget(
        TangleSlider(amount=18, min_value=1, max_value=60, step=0.5, suffix=" days")
    )
    # Shown from the defining cell so the widgets aren't re-rendered mid-drag.
    mo.md(f"""
    Designing the feature takes {design} and building it takes {build}.
    The deadline is in {deadline}.
    """)
    return build, deadline, design


@app.cell(hide_code=True)
def _(alt, build, deadline, design, mo, pd):
    # Committed params are the "before"; live params are what is being dragged now.
    _before = design.sample(5000, seed=0) + build.sample(5000, seed=1)
    _now = design.sample(5000, seed=0, live=True) + build.sample(5000, seed=1, live=True)
    _changing = design.dragging or build.dragging

    df_total = pd.concat([
        pd.DataFrame({"days": _before, "version": "before"}),
        pd.DataFrame({"days": _now, "version": "now"}),
    ]) if _changing else pd.DataFrame({"days": _now, "version": "now"})

    hist = (
        alt.Chart(df_total)
        .mark_bar(opacity=0.55)
        .encode(
            x=alt.X("days:Q").bin(alt.Bin(step=1)).title("total days"),
            y=alt.Y("count()").stack(None).title(None),
            color=alt.Color("version:N")
            .scale(domain=["before", "now"], range=["#8c959f", "#0066cc"])
            .legend(orient="top", title=None),
        )
    )
    rule = alt.Chart(pd.DataFrame({"days": [deadline.amount]})).mark_rule(color="firebrick", strokeWidth=2).encode(x="days:Q")

    p_before = (_before > deadline.amount).mean()
    p_now = (_now > deadline.amount).mean()
    summary = (
        f"Chance we ship late: **{p_before:.0%} → {p_now:.0%}**"
        if _changing
        else f"Chance we ship late: **{p_now:.0%}**"
    )
    mo.vstack([mo.md(summary), (hist + rule).properties(width=500, height=200)])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Probabilities and percentiles

    The widget answers the usual questions itself, for the supported families
    only:

    - `widget.cdf(x)`: the chance of a value at or below `x`.
    - `widget.ppf(q)`: the value below which a fraction `q` falls (the inverse of `cdf`).
    - `widget.pdf(x)` for continuous families, `widget.pmf(k)` for discrete ones.
    - `widget.sample(n)`: random draws (needs numpy).

    All of them accept arrays and `live=True` for the in-progress values while
    you drag. No scipy needed.
    """)
    return


@app.cell(hide_code=True)
def _(TangleDistribution, mo):
    delivery = mo.ui.anywidget(
        TangleDistribution("lognorm", params={"scale": 25, "s": 0.3}, template="{mean:.0f} ± {sd:.0f} minutes")
    )
    # Shown from the defining cell so the widget isn't re-rendered mid-drag.
    mo.md(f"A pizza delivery takes {delivery}.")
    return (delivery,)


@app.cell
def _(delivery, mo):
    mo.md(f"""
    - 90% of deliveries arrive within **{delivery.ppf(0.9, live=True):.0f} minutes** (`ppf(0.9)`).
    - The chance it arrives within half an hour is **{delivery.cdf(30, live=True):.0%}** (`cdf(30)`).
    """)
    return


if __name__ == "__main__":
    app.run()
