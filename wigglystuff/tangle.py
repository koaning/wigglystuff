import math
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anywidget
import traitlets

from ._distributions import FAMILIES, cdf, density, moments, ppf


class TangleSlider(anywidget.AnyWidget):
    """Inline slider inspired by Bret Victor's Tangle UI.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import TangleSlider

        slider = mo.ui.anywidget(TangleSlider(amount=50, min_value=0, max_value=100))
        slider
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-slider.js"
    amount = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    steps = traitlets.List(traitlets.Float(), default_value=[]).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)
    prefix = traitlets.Unicode("").tag(sync=True)
    suffix = traitlets.Unicode("").tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)

    _LINEAR_DEFAULTS = {"min_value": -100, "max_value": 100, "step": 1.0}

    def __init__(
        self,
        amount: Optional[float] = None,
        min_value: float = -100,
        max_value: float = 100,
        step: float = 1.0,
        steps: Optional[List[float]] = None,
        pixels_per_step: int = 2,
        prefix: str = "",
        suffix: str = "",
        digits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Create a slider suitable for inline Tangle interactions.

        Args:
            amount: Starting value; defaults to midpoint of bounds (linear mode)
                or first element (steps mode).
            min_value: Lower bound. Mutually exclusive with ``steps``.
            max_value: Upper bound. Mutually exclusive with ``steps``.
            step: Increment size. Mutually exclusive with ``steps``.
            steps: Explicit list of values to cycle through. When set,
                ``min_value``, ``max_value``, and ``step`` must not be provided.
            pixels_per_step: Drag distance per step.
            prefix: Text shown before the value.
            suffix: Text shown after the value.
            digits: Number formatting precision.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if steps is not None:
            steps = [float(v) for v in steps]
            linear_given = {
                k for k, v in self._LINEAR_DEFAULTS.items()
                if locals()[k] != v
            }
            if linear_given:
                raise ValueError(
                    f"Cannot use 'steps' together with {', '.join(sorted(linear_given))}."
                )
            if len(steps) < 2:
                raise ValueError("Must pass at least two steps.")
            if amount is not None and amount not in steps:
                raise ValueError(f"amount={amount} is not in the steps list.")
            if amount is None:
                amount = steps[0]
        else:
            steps = []
            if amount is None:
                amount = (max_value + min_value) / 2
        super().__init__(
            amount=amount,
            min_value=min_value,
            max_value=max_value,
            step=step,
            steps=steps,
            pixels_per_step=pixels_per_step,
            prefix=prefix,
            suffix=suffix,
            digits=digits,
            **kwargs,
        )


def _default_step(value: float) -> float:
    """The power of ten closest to a fiftieth of the starting magnitude."""
    if value == 0:
        return 0.1
    return 10 ** round(math.log10(abs(value) / 50))


def _elementwise(fn, x):
    """Apply a scalar function to a scalar or array-like, numpy-style."""
    import numpy as np

    out = np.vectorize(fn, otypes=[float])(np.asarray(x, dtype=float))
    return float(out) if out.ndim == 0 else out


class TangleDistribution(anywidget.AnyWidget):
    """Inline tangle number that carries a whole distribution.

    Drag left/right to change the first parameter and up/down to change the
    second. While dragging, a small chart of the distribution floats above the
    page so you can see the shape change. Family and parameter names follow
    ``scipy.stats``, but only the families below are supported (see
    ``TangleDistribution.distributions``), and the maths is built in, so scipy
    is not needed.

    | family | kind | ↔ drag | ↕ drag |
    | --- | --- | --- | --- |
    | ``"norm"`` | continuous | ``loc`` | ``scale`` |
    | ``"lognorm"`` | continuous | ``scale`` (the median) | ``s`` |
    | ``"gamma"`` | continuous | ``scale`` | ``a`` (the shape) |
    | ``"expon"`` | continuous | ``scale`` (the mean) | (none) |
    | ``"weibull_min"`` | continuous | ``scale`` | ``c`` (the shape) |
    | ``"uniform"`` | continuous | ``loc`` (left edge) | ``scale`` (width) |
    | ``"laplace"`` | continuous | ``loc`` | ``scale`` |
    | ``"logistic"`` | continuous | ``loc`` | ``scale`` |
    | ``"beta"`` | continuous | ``a`` | ``b`` |
    | ``"poisson"`` | discrete | ``mu`` | (none) |
    | ``"binom"`` | discrete | ``p`` | ``n`` (whole number) |
    | ``"nbinom"`` | discrete | ``p`` | ``n`` |
    | ``"geom"`` | discrete | ``p`` | (none) |
    | ``"randint"`` | discrete | ``low`` | ``high`` (excluded, as in scipy) |

    Template fields are the parameters in the table plus ``mean`` and ``sd``.

    Reading the distribution back in Python:

    - ``params`` holds the committed values and only changes when a drag is
      released. While dragging, ``live_params`` follows the pointer (throttled
      by ``sync_throttle_ms``) and ``dragging`` is True, so the rest of the
      notebook can compare the old distribution against the new one live.
    - ``mean`` and ``sd`` are computed from ``params``.
    - ``pdf(x)`` (continuous) or ``pmf(k)`` (discrete), ``cdf(x)``,
      ``ppf(q)`` and ``sample(n)`` all accept ``live=True`` to use
      ``live_params`` instead. ``sample`` needs numpy, as do the others when
      given an array.

    The inline text comes from ``template``, by default ``"{mean} ± {sd}"``.
    Placeholders are the keys of ``params`` plus the computed ``mean`` and
    ``sd`` (``widget.template_fields`` lists them), each with an optional
    ``:.Nf`` precision, e.g. ``"median {scale:.0f} days (s={s:.2f})"``.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import TangleDistribution

        duration = mo.ui.anywidget(
            TangleDistribution("lognorm", params={"scale": 10, "s": 0.4}, template="{mean} ± {sd} days")
        )
        duration
        ```

        ```python
        duration.ppf(0.9)  # 90% of runs finish within this many days
        duration.cdf(14)   # chance of finishing within two weeks
        ```
    """

    distributions = tuple(FAMILIES)

    _esm = Path(__file__).parent / "static" / "tangle-distribution.js"
    distribution = traitlets.Unicode("norm").tag(sync=True)
    params = traitlets.Dict().tag(sync=True)
    live_params = traitlets.Dict().tag(sync=True)
    bounds = traitlets.Dict().tag(sync=True)
    steps = traitlets.Dict().tag(sync=True)
    dragging = traitlets.Bool(False).tag(sync=True)
    sync_throttle_ms = traitlets.Int(100).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)
    template = traitlets.Unicode("{mean} ± {sd}").tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)

    def __init__(
        self,
        distribution: str = "norm",
        params: Optional[Dict[str, float]] = None,
        bounds: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None,
        steps: Optional[Dict[str, float]] = None,
        pixels_per_step: int = 2,
        template: str = "{mean} ± {sd}",
        digits: Optional[int] = None,
        sync_throttle_ms: int = 100,
        **kwargs: Any,
    ) -> None:
        """Create an inline distribution control.

        Args:
            distribution: One of ``TangleDistribution.distributions``, see
                the table above.
            params: Starting parameters by scipy name; missing ones use the
                family default.
            bounds: Optional ``(low, high)`` per parameter; either end may be
                ``None``. Defaults: ``loc`` and randint's ``low``/``high`` are
                unbounded, a probability like ``p`` stays inside
                ``(step, 1 - step)``, binom's ``n`` is at least 1, and
                everything else stays positive with ``(step, None)``.
            steps: Change per drag step, per parameter. Defaults to 1 for whole
                numbers and otherwise a power of ten that suits the starting
                value.
            pixels_per_step: Drag distance per step (both directions).
            template: Inline text. ``{name}`` placeholders take any parameter
                of the family plus ``mean`` and ``sd`` (see ``template_fields``);
                add ``:.Nf`` (e.g. ``{mean:.0f}``) to override ``digits`` for
                that placeholder.
            digits: Default number of decimals in the inline text; defaults
                to what the smallest step and the starting sd need. Whole
                number parameters always show without decimals.
            sync_throttle_ms: Cap on how often ``live_params`` reaches Python
                while dragging, in milliseconds. ``0`` syncs every move.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if distribution not in FAMILIES:
            raise ValueError(
                f"distribution={distribution!r} is not supported; pick one of {list(FAMILIES)}."
            )
        spec = FAMILIES[distribution]
        names = list(spec["params"])
        params, bounds, steps = dict(params or {}), dict(bounds or {}), dict(steps or {})
        for given in (params, bounds, steps):
            unknown = set(given) - set(names)
            if unknown:
                raise ValueError(
                    f"{distribution!r} has parameters {names}; got unknown {sorted(unknown)}."
                )

        full_params, full_bounds, full_steps = {}, {}, {}
        for name in names:
            value = params.get(name, spec["params"][name])
            unbounded = name in spec.get("unbounded", [])
            if name in spec.get("integer", []):
                if value != int(value):
                    raise ValueError(f"{name!r} must be a whole number, got {value}.")
                value = int(value)
                step = steps.get(name, 1)
                if step != int(step) or step < 1:
                    raise ValueError(f"The step for {name!r} must be a whole number of at least 1.")
                step = int(step)
                low, high = bounds.get(name, (None, None) if unbounded else (1, None))
                if not unbounded and (low is None or low < 1):
                    raise ValueError(f"The lower bound for {name!r} must be at least 1.")
            elif name in spec.get("probability", []):
                value = float(value)
                step = float(steps.get(name, _default_step(value)))
                low, high = bounds.get(name, (step, 1 - step))
                if low is None or high is None or low <= 0 or high >= 1:
                    raise ValueError(f"The bounds for {name!r} must lie strictly between 0 and 1.")
            else:
                value = float(value)
                step = float(steps.get(name, _default_step(value)))
                low, high = bounds.get(name, (None, None) if unbounded else (step, None))
                if not unbounded and (low is None or low <= 0):
                    raise ValueError(f"The lower bound for {name!r} must be positive.")
            if (low is not None and value < low) or (high is not None and value > high):
                raise ValueError(f"{name}={value} is outside the bounds ({low}, {high}).")
            full_params[name], full_bounds[name], full_steps[name] = value, [low, high], step

        if distribution == "randint" and full_params["low"] >= full_params["high"]:
            raise ValueError("randint needs low < high (high itself is excluded, as in scipy).")

        allowed = names + ["mean", "sd"]
        for _, field, fmt_spec, _ in string.Formatter().parse(template):
            if field is None:
                continue
            if field not in allowed:
                raise ValueError(
                    f"Unknown placeholder {{{field}}} in template; {distribution!r} supports {allowed}."
                )
            if fmt_spec and not re.fullmatch(r"\.\d+f", fmt_spec):
                raise ValueError(f"Only '.Nf' precision is supported in the template, got {fmt_spec!r}.")

        if digits is None:
            # Enough decimals for the finest drag step, and for two significant
            # figures of the starting sd so "{mean} ± {sd}" never reads "0.3 ± 0.2".
            step_digits = max(-math.floor(math.log10(s)) for s in full_steps.values())
            sd = moments(distribution, full_params)[1]
            sd_digits = 1 - math.floor(math.log10(sd)) if sd > 0 else 0  # randint can have one value
            digits = max(0, step_digits, sd_digits)

        super().__init__(
            distribution=distribution,
            params=full_params,
            live_params=dict(full_params),
            bounds=full_bounds,
            steps=full_steps,
            pixels_per_step=pixels_per_step,
            template=template,
            digits=digits,
            sync_throttle_ms=sync_throttle_ms,
            **kwargs,
        )

    @traitlets.observe("params")
    def _follow_committed(self, change: dict) -> None:
        # A Python-side change to params outside a drag moves the live ones too.
        if not self.dragging:
            self.live_params = dict(self.params)

    @property
    def discrete(self) -> bool:
        """True for families over whole numbers (``poisson``, ``binom``, ``nbinom``, ``geom``, ``randint``)."""
        return bool(FAMILIES[self.distribution].get("discrete"))

    @property
    def template_fields(self) -> List[str]:
        """Placeholders ``template`` accepts: the family's parameters plus ``mean`` and ``sd``."""
        return list(FAMILIES[self.distribution]["params"]) + ["mean", "sd"]

    @property
    def mean(self) -> float:
        """Mean of the committed distribution."""
        return moments(self.distribution, self.params)[0]

    @property
    def sd(self) -> float:
        """Standard deviation of the committed distribution."""
        return moments(self.distribution, self.params)[1]

    def _p(self, live: bool) -> Dict[str, float]:
        return self.live_params if live else self.params

    def pdf(self, x, live: bool = False):
        """Probability density at ``x`` (scalar or array-like); continuous families only."""
        if self.discrete:
            raise TypeError(f"{self.distribution!r} is discrete; use pmf(k) instead of pdf(x).")
        p = self._p(live)
        return _elementwise(lambda v: density(self.distribution, p, v), x)

    def pmf(self, k, live: bool = False):
        """Probability of exactly ``k`` (scalar or array-like); discrete families only."""
        if not self.discrete:
            raise TypeError(f"{self.distribution!r} is continuous; use pdf(x) instead of pmf(k).")
        p = self._p(live)
        return _elementwise(lambda v: density(self.distribution, p, v), k)

    def cdf(self, x, live: bool = False):
        """Probability of a value at or below ``x`` (scalar or array-like)."""
        p = self._p(live)
        return _elementwise(lambda v: cdf(self.distribution, p, v), x)

    def ppf(self, q, live: bool = False):
        """Value below which a fraction ``q`` of the distribution lies (inverse of ``cdf``)."""
        p = self._p(live)
        return _elementwise(lambda v: ppf(self.distribution, p, v), q)

    def sample(self, n: int, seed: Optional[int] = None, live: bool = False):
        """Draw ``n`` samples as a numpy array."""
        import numpy as np

        p = self._p(live)
        rng = np.random.default_rng(seed)
        if self.distribution == "norm":
            return rng.normal(p["loc"], p["scale"], size=n)
        if self.distribution == "lognorm":
            return rng.lognormal(math.log(p["scale"]), p["s"], size=n)
        if self.distribution == "gamma":
            return rng.gamma(p["a"], p["scale"], size=n)
        if self.distribution == "expon":
            return rng.exponential(p["scale"], size=n)
        if self.distribution == "weibull_min":
            return p["scale"] * rng.weibull(p["c"], size=n)
        if self.distribution == "laplace":
            return rng.laplace(p["loc"], p["scale"], size=n)
        if self.distribution == "logistic":
            return rng.logistic(p["loc"], p["scale"], size=n)
        if self.distribution == "uniform":
            return rng.uniform(p["loc"], p["loc"] + p["scale"], size=n)
        if self.distribution == "beta":
            return rng.beta(p["a"], p["b"], size=n)
        if self.distribution == "poisson":
            return rng.poisson(p["mu"], size=n)
        if self.distribution == "binom":
            return rng.binomial(int(p["n"]), p["p"], size=n)
        if self.distribution == "nbinom":
            return rng.negative_binomial(p["n"], p["p"], size=n)
        if self.distribution == "geom":
            return rng.geometric(p["p"], size=n)
        return rng.integers(int(p["low"]), int(p["high"]), size=n)


class TangleChoice(anywidget.AnyWidget):
    """Inline choice widget that cycles through labeled options.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import TangleChoice

        choice = mo.ui.anywidget(TangleChoice(choices=["small", "medium", "large"]))
        choice
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-choice.js"
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs: Any) -> None:
        """Create a TangleChoice widget.

        Args:
            choices: Ordered sequence of options (min two).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(choice=choices[0], choices=choices, **kwargs)


class TangleSelect(anywidget.AnyWidget):
    """Dropdown-based take on the Tangle choice pattern.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import TangleSelect

        select = mo.ui.anywidget(TangleSelect(choices=["red", "green", "blue"]))
        select
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-select.js"
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs: Any) -> None:
        """Create a TangleSelect dropdown.

        Args:
            choices: Ordered sequence of options (min two).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(choice=choices[0], choices=choices, **kwargs)
