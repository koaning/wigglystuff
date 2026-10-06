"""Tests for the TangleDistribution widget and its built-in distribution maths."""

import math

import numpy as np
import pytest

from wigglystuff import TangleDistribution

# One or more parameter sets per family, including awkward shapes (a < 1, heavy
# tails, large n, tiny p) where the incomplete gamma/beta code has to work hard.
CASES = [
    ("norm", {"loc": 50, "scale": 10}),
    ("lognorm", {"scale": 20, "s": 0.5}),
    ("gamma", {"scale": 3, "a": 2}),
    ("gamma", {"scale": 2, "a": 0.5}),
    ("expon", {"scale": 4}),
    ("weibull_min", {"scale": 10, "c": 1.5}),
    ("weibull_min", {"scale": 2, "c": 0.7}),
    ("uniform", {"loc": 40, "scale": 20}),
    ("laplace", {"loc": 3, "scale": 2}),
    ("logistic", {"loc": -1, "scale": 0.5}),
    ("beta", {"a": 2, "b": 5}),
    ("beta", {"a": 0.5, "b": 0.5}),
    ("poisson", {"mu": 4}),
    ("poisson", {"mu": 300}),
    ("binom", {"p": 0.3, "n": 20}),
    ("binom", {"p": 0.02, "n": 1000}),
    ("nbinom", {"p": 0.3, "n": 5}),
    ("nbinom", {"p": 0.05, "n": 2.5}),
    ("geom", {"p": 0.2}),
    ("geom", {"p": 0.01}),
    ("randint", {"low": -3, "high": 7}),
]
IDS = [f"{name}-{'-'.join(f'{k}{v}' for k, v in p.items())}" for name, p in CASES]


def test_every_family_is_covered():
    assert {name for name, _ in CASES} == set(TangleDistribution.distributions)


@pytest.mark.parametrize(("name", "params"), CASES, ids=IDS)
def test_matches_scipy(name, params):
    """mean, sd, pdf/pmf, cdf and ppf agree with scipy.stats to near machine precision."""
    stats = pytest.importorskip("scipy.stats")
    w = TangleDistribution(name, params=params)
    ref = getattr(stats, name)(**params)

    assert w.mean == pytest.approx(ref.mean(), rel=1e-9, abs=1e-12)
    assert w.sd == pytest.approx(ref.std(), rel=1e-9, abs=1e-12)

    lo, hi = ref.ppf(0.001), ref.ppf(0.999)
    if w.discrete:
        # Include points just outside the support, which must carry no mass.
        x = np.arange(np.floor(lo) - 2, np.ceil(hi) + 3)
        np.testing.assert_allclose(w.pmf(x), ref.pmf(x), rtol=1e-9, atol=1e-12)
    else:
        x = np.linspace(lo, hi, 101)
        np.testing.assert_allclose(w.pdf(x), ref.pdf(x), rtol=1e-9, atol=1e-12)
    np.testing.assert_allclose(w.cdf(x), ref.cdf(x), rtol=1e-9, atol=1e-12)

    q = np.array([0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999])
    np.testing.assert_allclose(w.ppf(q), ref.ppf(q), rtol=1e-9, atol=1e-9)


@pytest.mark.parametrize(("name", "params"), CASES, ids=IDS)
def test_density_is_normalised_and_cdf_is_consistent(name, params):
    """Without scipy: the density sums to 1, the cdf rises from 0 to 1, and ppf inverts it."""
    w = TangleDistribution(name, params=params)
    lo, hi = w.ppf(1e-6), w.ppf(1 - 1e-6)
    if w.discrete:
        k = np.arange(lo, hi + 1)
        assert w.pmf(k).sum() == pytest.approx(1, abs=1e-5)
        # cdf is the running sum of the pmf.
        np.testing.assert_allclose(w.cdf(k), np.cumsum(w.pmf(k)) + w.cdf(lo - 1), atol=1e-9)
    else:
        # Substitute x = lo + (hi - lo)(1 - cos(pi t)) / 2, which bunches points at
        # both ends, so densities that spike at an edge (gamma a < 1, weibull
        # c < 1, beta(0.5, 0.5)) still integrate cleanly with the midpoint rule.
        t = (np.arange(200_000) + 0.5) / 200_000
        x = lo + (hi - lo) * (1 - np.cos(np.pi * t)) / 2
        dx_dt = (hi - lo) * np.pi / 2 * np.sin(np.pi * t)
        assert np.mean(w.pdf(x) * dx_dt) == pytest.approx(1, abs=2e-3)

    grid = np.linspace(lo, hi, 300)
    c = w.cdf(grid)
    assert np.all(np.diff(c) >= -1e-15)
    assert c[0] >= 0 and c[-1] <= 1
    # ppf(cdf(x)) gets back to x for continuous families...
    if not w.discrete:
        inner = np.linspace(w.ppf(0.01), w.ppf(0.99), 25)
        np.testing.assert_allclose(w.ppf(w.cdf(inner)), inner, rtol=1e-7, atol=1e-7)
    # ...and for every family ppf(q) is the smallest value with cdf >= q.
    for q in (0.05, 0.5, 0.95):
        v = w.ppf(q)
        assert w.cdf(v) >= q - 1e-9
        if w.discrete:
            assert w.cdf(v - 1) < q


@pytest.mark.parametrize(("name", "params"), CASES, ids=IDS)
def test_samples_match_mean_and_sd(name, params):
    w = TangleDistribution(name, params=params)
    draws = w.sample(200_000, seed=0)
    assert draws.shape == (200_000,)
    se = w.sd / math.sqrt(len(draws))
    assert abs(draws.mean() - w.mean) < 6 * se + 1e-12
    assert draws.std() == pytest.approx(w.sd, rel=0.03)
    low, high = w.ppf(0), w.ppf(1)
    assert draws.min() >= low and draws.max() <= high
    if w.discrete:
        assert np.all(draws == np.round(draws))


def test_defaults_and_discovery():
    w = TangleDistribution()
    assert w.distribution == "norm"
    assert w.params == {"loc": 0.0, "scale": 1.0}
    assert w.live_params == w.params
    assert w.dragging is False
    assert w.template == "{mean} ± {sd}"
    assert w.template_fields == ["loc", "scale", "mean", "sd"]
    assert TangleDistribution("binom").template_fields == ["p", "n", "mean", "sd"]
    assert TangleDistribution("poisson").discrete and not TangleDistribution("gamma").discrete
    assert len(TangleDistribution.distributions) == 14
    # Missing parameters fall back to the family default.
    assert TangleDistribution("gamma", params={"a": 3}).params == {"scale": 1.0, "a": 3.0}


def test_default_bounds_steps_and_digits():
    norm = TangleDistribution("norm", params={"loc": 50, "scale": 10})
    assert norm.bounds == {"loc": [None, None], "scale": [0.1, None]}
    assert norm.steps == {"loc": 1.0, "scale": 0.1}
    assert norm.digits == 1  # "50.0 ± 10.0"
    # Two significant figures of the sd, so beta doesn't read "0.3 ± 0.2".
    assert TangleDistribution("beta", params={"a": 2, "b": 5}).digits == 2
    binom = TangleDistribution("binom", params={"p": 0.3, "n": 20})
    assert binom.bounds == {"p": [0.01, 0.99], "n": [1, None]}
    assert binom.steps["n"] == 1 and isinstance(binom.params["n"], int)
    assert TangleDistribution("randint").bounds == {"low": [None, None], "high": [None, None]}
    # A single-valued randint has sd 0; that must not break the digits default.
    single = TangleDistribution("randint", params={"low": 0, "high": 1})
    assert (single.sd, single.ppf(0.5), single.pmf(0)) == (0.0, 0.0, 1.0)
    assert TangleDistribution("norm", digits=4).digits == 4


def test_invalid_arguments_raise():
    bad = [
        dict(distribution="t"),
        dict(distribution="norm", params={"mu": 1}),
        dict(distribution="norm", bounds={"sigma": (0, 1)}),
        dict(distribution="norm", params={"scale": -1}),
        dict(distribution="norm", bounds={"scale": (0, 5)}),
        dict(distribution="norm", params={"loc": 5}, bounds={"loc": (0, 1)}),
        dict(distribution="binom", params={"n": 2.5}),
        dict(distribution="binom", steps={"n": 0.5}),
        dict(distribution="binom", bounds={"p": (0, 1)}),
        dict(distribution="randint", params={"low": 5, "high": 5}),
        dict(distribution="randint", params={"low": 1.5}),
        dict(distribution="gamma", template="{loc}"),
        dict(distribution="norm", template="{mean:,.2f}"),
        dict(distribution="norm", template="{mean:.0%}"),
    ]
    for kwargs in bad:
        with pytest.raises(ValueError):
            TangleDistribution(**kwargs)
    with pytest.raises(ValueError, match=r"'gamma' supports \['scale', 'a', 'mean', 'sd'\]"):
        TangleDistribution("gamma", template="{loc}")
    TangleDistribution("lognorm", template="median {scale:.0f} days (s={s:.2f})")  # valid


def test_pdf_and_pmf_are_kind_specific():
    with pytest.raises(TypeError, match="pmf"):
        TangleDistribution("poisson").pdf(3)
    with pytest.raises(TypeError, match="pdf"):
        TangleDistribution("norm").pmf(3)
    # Off-integer points carry no mass.
    assert TangleDistribution("poisson").pmf(2.5) == 0.0


def test_scalars_in_scalars_out_arrays_in_arrays_out():
    w = TangleDistribution("norm", params={"loc": 0, "scale": 1})
    assert isinstance(w.pdf(0.0), float)
    assert isinstance(w.cdf(0.0), float)
    assert isinstance(w.ppf(0.5), float)
    assert w.cdf(0.0) == pytest.approx(0.5)
    assert w.pdf([0, 1, 2]).shape == (3,)
    assert w.ppf(np.array([[0.1, 0.9]])).shape == (1, 2)


def test_ppf_edges():
    w = TangleDistribution("gamma", params={"a": 2, "scale": 3})
    assert w.ppf(0) == 0 and w.ppf(1) == math.inf
    assert math.isnan(w.ppf(-0.1)) and math.isnan(w.ppf(1.5))
    u = TangleDistribution("uniform", params={"loc": 40, "scale": 20})
    assert (u.ppf(0), u.ppf(1)) == (40, 60)
    g = TangleDistribution("geom", params={"p": 0.2})
    # cdf(1) = 0.2 already exceeds q here; this used to loop forever.
    assert g.ppf(0.1) == 1.0


def test_live_params_follow_committed_outside_drags():
    w = TangleDistribution("norm", params={"loc": 0, "scale": 1})
    w.params = {"loc": 5.0, "scale": 2.0}
    assert w.live_params == {"loc": 5.0, "scale": 2.0}

    # Mid-drag the frontend moves only live_params; Python must not overwrite them.
    w.dragging = True
    w.live_params = {"loc": 9.0, "scale": 3.0}
    w.params = {"loc": 6.0, "scale": 2.0}
    assert w.live_params == {"loc": 9.0, "scale": 3.0}

    # Committed and live answers differ while the drag is in progress.
    assert w.mean == 6.0 and w.sd == 2.0
    assert w.cdf(9.0, live=True) == pytest.approx(0.5)
    assert w.ppf(0.5, live=True) == pytest.approx(9.0)
    assert w.pdf(6.0) == pytest.approx(1 / (2 * math.sqrt(2 * math.pi)))
    assert w.sample(50_000, seed=0, live=True).mean() == pytest.approx(9.0, abs=0.05)
    assert w.sample(50_000, seed=0).mean() == pytest.approx(6.0, abs=0.05)
