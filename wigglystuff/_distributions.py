"""Plain-``math`` maths for the families ``TangleDistribution`` supports.

Names and parameters follow ``scipy.stats`` so the numbers mean the same thing,
but nothing here needs scipy (or numpy). Every function works on one scalar;
the widget vectorises them when it is handed an array.
"""

import math
from typing import Dict, Tuple

# Each family lists its scipy parameters with their default values; the first
# is dragged horizontally and the second (if any) vertically. Parameters are
# positive unless marked: ``unbounded`` may be any number, ``probability`` lies
# strictly between 0 and 1, and ``integer`` only takes whole numbers.
FAMILIES = {
    "norm": {"params": {"loc": 0.0, "scale": 1.0}, "unbounded": ["loc"]},
    "lognorm": {"params": {"scale": 1.0, "s": 0.5}},
    "gamma": {"params": {"scale": 1.0, "a": 2.0}},
    "expon": {"params": {"scale": 1.0}},
    "weibull_min": {"params": {"scale": 1.0, "c": 1.5}},
    "uniform": {"params": {"loc": 0.0, "scale": 1.0}, "unbounded": ["loc"]},
    "laplace": {"params": {"loc": 0.0, "scale": 1.0}, "unbounded": ["loc"]},
    "logistic": {"params": {"loc": 0.0, "scale": 1.0}, "unbounded": ["loc"]},
    "beta": {"params": {"a": 2.0, "b": 2.0}},
    "poisson": {"params": {"mu": 4.0}, "discrete": True},
    "binom": {"params": {"p": 0.5, "n": 10}, "discrete": True, "integer": ["n"], "probability": ["p"]},
    "nbinom": {"params": {"p": 0.5, "n": 5.0}, "discrete": True, "probability": ["p"]},
    "geom": {"params": {"p": 0.2}, "discrete": True, "probability": ["p"]},
    "randint": {
        "params": {"low": 0, "high": 10},
        "discrete": True,
        "integer": ["low", "high"],
        "unbounded": ["low", "high"],
    },
}

_TINY = 1e-300


def moments(distribution: str, p: Dict[str, float]) -> Tuple[float, float]:
    """Mean and standard deviation."""
    if distribution == "norm":
        return p["loc"], p["scale"]
    if distribution == "lognorm":
        e = math.exp(p["s"] ** 2)
        return p["scale"] * math.sqrt(e), p["scale"] * math.sqrt((e - 1) * e)
    if distribution == "gamma":
        return p["a"] * p["scale"], math.sqrt(p["a"]) * p["scale"]
    if distribution == "expon":
        return p["scale"], p["scale"]
    if distribution == "weibull_min":
        g1, g2 = math.gamma(1 + 1 / p["c"]), math.gamma(1 + 2 / p["c"])
        return p["scale"] * g1, p["scale"] * math.sqrt(g2 - g1 * g1)
    if distribution == "uniform":
        return p["loc"] + p["scale"] / 2, p["scale"] / math.sqrt(12)
    if distribution == "laplace":
        return p["loc"], math.sqrt(2) * p["scale"]
    if distribution == "logistic":
        return p["loc"], p["scale"] * math.pi / math.sqrt(3)
    if distribution == "beta":
        a, b = p["a"], p["b"]
        return a / (a + b), math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
    if distribution == "poisson":
        return p["mu"], math.sqrt(p["mu"])
    if distribution == "binom":
        n, q = p["n"], p["p"]
        return n * q, math.sqrt(n * q * (1 - q))
    if distribution == "nbinom":
        n, q = p["n"], p["p"]
        return n * (1 - q) / q, math.sqrt(n * (1 - q)) / q
    if distribution == "geom":
        q = p["p"]
        return 1 / q, math.sqrt(1 - q) / q
    # randint: whole numbers low, ..., high - 1
    width = p["high"] - p["low"]
    return (p["low"] + p["high"] - 1) / 2, math.sqrt((width * width - 1) / 12)


def support(distribution: str, p: Dict[str, float]) -> Tuple[float, float]:
    """Smallest and largest possible value."""
    if distribution in ("norm", "laplace", "logistic"):
        return -math.inf, math.inf
    if distribution in ("lognorm", "gamma", "expon", "weibull_min", "poisson", "nbinom"):
        return 0.0, math.inf
    if distribution == "uniform":
        return p["loc"], p["loc"] + p["scale"]
    if distribution == "beta":
        return 0.0, 1.0
    if distribution == "binom":
        return 0.0, float(p["n"])
    if distribution == "geom":
        return 1.0, math.inf
    return float(p["low"]), float(p["high"] - 1)


def density(distribution: str, p: Dict[str, float], x: float) -> float:
    """pdf for continuous families, pmf for discrete ones."""
    low, high = support(distribution, p)
    if not low <= x <= high:
        return 0.0
    if distribution == "norm":
        z = (x - p["loc"]) / p["scale"]
        return math.exp(-0.5 * z * z) / (p["scale"] * math.sqrt(2 * math.pi))
    if distribution == "lognorm":
        if x == 0:
            return 0.0
        z = (math.log(x) - math.log(p["scale"])) / p["s"]
        return math.exp(-0.5 * z * z) / (x * p["s"] * math.sqrt(2 * math.pi))
    if distribution == "gamma":
        a, scale = p["a"], p["scale"]
        if x == 0:
            return math.inf if a < 1 else (1 / scale if a == 1 else 0.0)
        return math.exp((a - 1) * math.log(x) - x / scale - math.lgamma(a) - a * math.log(scale))
    if distribution == "expon":
        return math.exp(-x / p["scale"]) / p["scale"]
    if distribution == "weibull_min":
        c, scale = p["c"], p["scale"]
        if x == 0:
            return math.inf if c < 1 else (1 / scale if c == 1 else 0.0)
        z = x / scale
        return (c / scale) * z ** (c - 1) * math.exp(-(z**c))
    if distribution == "uniform":
        return 1.0 / p["scale"]
    if distribution == "laplace":
        return math.exp(-abs(x - p["loc"]) / p["scale"]) / (2 * p["scale"])
    if distribution == "logistic":
        # 1 / (4 cosh^2(z / 2)) is the stable form of e^-z / (1 + e^-z)^2.
        z = (x - p["loc"]) / p["scale"]
        if abs(z) > 700:
            return 0.0
        return 1 / (4 * p["scale"] * math.cosh(z / 2) ** 2)
    if distribution == "beta":
        if x in (0.0, 1.0):
            return 0.0
        a, b = p["a"], p["b"]
        log_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        return math.exp((a - 1) * math.log(x) + (b - 1) * math.log1p(-x) - log_beta)

    # Discrete: only whole numbers inside the support carry probability.
    if x != math.floor(x):
        return 0.0
    k = int(x)
    if distribution == "poisson":
        mu = p["mu"]
        return math.exp(k * math.log(mu) - mu - math.lgamma(k + 1))
    if distribution == "binom":
        n, q = int(p["n"]), p["p"]
        log_choose = math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        return math.exp(log_choose + k * math.log(q) + (n - k) * math.log1p(-q))
    if distribution == "nbinom":
        n, q = p["n"], p["p"]
        log_choose = math.lgamma(k + n) - math.lgamma(n) - math.lgamma(k + 1)
        return math.exp(log_choose + n * math.log(q) + k * math.log1p(-q))
    if distribution == "geom":
        q = p["p"]
        return math.exp((k - 1) * math.log1p(-q)) * q
    return 1 / (p["high"] - p["low"])


def cdf(distribution: str, p: Dict[str, float], x: float) -> float:
    """P(X <= x)."""
    low, high = support(distribution, p)
    if x < low:
        return 0.0
    if x >= high:
        return 1.0
    if distribution == "norm":
        return _norm_cdf((x - p["loc"]) / p["scale"])
    if distribution == "lognorm":
        return 0.0 if x == 0 else _norm_cdf((math.log(x) - math.log(p["scale"])) / p["s"])
    if distribution == "gamma":
        return _gammainc(p["a"], x / p["scale"])
    if distribution == "expon":
        return -math.expm1(-x / p["scale"])
    if distribution == "weibull_min":
        return -math.expm1(-((x / p["scale"]) ** p["c"]))
    if distribution == "uniform":
        return (x - p["loc"]) / p["scale"]
    if distribution == "laplace":
        z = (x - p["loc"]) / p["scale"]
        return 0.5 * math.exp(z) if z < 0 else 1 - 0.5 * math.exp(-z)
    if distribution == "logistic":
        z = (x - p["loc"]) / p["scale"]
        return 1 / (1 + math.exp(-z)) if z > -700 else 0.0
    if distribution == "beta":
        return _betainc(p["a"], p["b"], x)

    # Discrete families have closed forms, so large means stay fast.
    k = math.floor(x)
    if distribution == "poisson":
        return 1 - _gammainc(k + 1, p["mu"])
    if distribution == "binom":
        return _betainc(p["n"] - k, k + 1, 1 - p["p"])
    if distribution == "nbinom":
        return _betainc(p["n"], k + 1, p["p"])
    if distribution == "geom":
        return -math.expm1(k * math.log1p(-p["p"]))
    return (k - p["low"] + 1) / (p["high"] - p["low"])


def ppf(distribution: str, p: Dict[str, float], q: float) -> float:
    """Inverse of the cdf: the smallest x with P(X <= x) >= q."""
    if not 0 <= q <= 1:
        return math.nan
    low, high = support(distribution, p)
    if q == 0:
        return low
    if q == 1:
        return high
    # Bracket q around mean ± sd, widening as needed, then bisect.
    mean, sd = moments(distribution, p)
    # Stop at the edge of the support: a discrete family can have cdf(low) > q.
    width = sd
    lo = max(low, mean - width)
    while lo > low and cdf(distribution, p, lo) > q:
        width *= 2
        lo = max(low, mean - width)
    width = sd
    hi = min(high, mean + width)
    while hi < high and cdf(distribution, p, hi) < q:
        width *= 2
        hi = min(high, mean + width)
    if FAMILIES[distribution].get("discrete"):
        # Smallest whole number k with cdf(k) >= q, allowing for rounding.
        lo, hi = math.floor(lo), math.ceil(hi)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cdf(distribution, p, mid) >= q - 1e-12:
                hi = mid
            else:
                lo = mid
        return float(lo if cdf(distribution, p, lo) >= q - 1e-12 else hi)
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(distribution, p, mid) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-12 * max(1.0, abs(mid)):
            break
    return (lo + hi) / 2


def _norm_cdf(z: float) -> float:
    return 0.5 * math.erfc(-z / math.sqrt(2))


def _gammainc(a: float, x: float) -> float:
    """Regularised lower incomplete gamma P(a, x) (Numerical Recipes 6.2)."""
    if x <= 0:
        return 0.0
    log_front = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1:
        # Series expansion converges quickly here.
        term = total = 1.0 / a
        ap = a
        for _ in range(1000):
            ap += 1
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return total * math.exp(log_front)
    # Continued fraction for the upper tail, evaluated with Lentz's method.
    b = x + 1 - a
    c = 1 / _TINY
    d = 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = _TINY if abs(d) < _TINY else d
        c = b + an / c
        c = _TINY if abs(c) < _TINY else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return 1 - math.exp(log_front) * h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b) (Numerical Recipes 6.4)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                 + a * math.log(x) + b * math.log1p(-x))
    # The continued fraction converges fast on this side; use symmetry otherwise.
    if x < (a + 1) / (a + b + 2):
        return math.exp(log_front) * _betacf(a, b, x) / a
    return 1 - math.exp(log_front) * _betacf(b, a, 1 - x) / b


def _betacf(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1, a - 1
    c = 1.0
    d = 1 - qab * x / qap
    d = 1 / (_TINY if abs(d) < _TINY else d)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (_TINY if abs(d) < _TINY else d)
        c = 1 + aa / c
        c = _TINY if abs(c) < _TINY else c
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (_TINY if abs(d) < _TINY else d)
        c = 1 + aa / c
        c = _TINY if abs(c) < _TINY else c
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return h
