"""GPU-accelerated 2D iterative-map attractor renderer."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets

_ALLOWED_FUNCS = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "atan2",
        "exp",
        "log",
        "sqrt",
        "abs",
        "floor",
        "sign",
        "min",
        "max",
        "pow",
    }
)
_ALLOWED_CONSTS = frozenset({"pi", "e"})
_ALLOWED_VARS = frozenset({"x", "y"})
_ALLOWED_BACKGROUNDS = frozenset({"black", "white"})
_ALLOWED_COLORMAPS = frozenset(
    {"phase", "magma", "viridis", "inferno", "plasma", "grayscale"}
)

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _validate_expr(expr: str, param_names: set[str], label: str) -> None:
    if not isinstance(expr, str) or not expr.strip():
        raise traitlets.TraitError(f"{label} must be a non-empty string.")
    allowed = _ALLOWED_FUNCS | _ALLOWED_CONSTS | _ALLOWED_VARS | param_names
    for ident in _IDENT_RE.findall(expr):
        if ident not in allowed:
            raise traitlets.TraitError(
                f"{label} references unknown identifier '{ident}'. "
                f"Allowed: x, y, {sorted(param_names)}, "
                f"functions {sorted(_ALLOWED_FUNCS)}, constants pi/e."
            )


class AttractorWidget(anywidget.AnyWidget):
    """GPU-accelerated renderer for 2D iterative-map attractors.

    Iterates a user-supplied formula (e.g. Clifford, De Jong) entirely on the
    JavaScript side, so changing parameters from Python is cheap. Renders with
    WebGL2 when available, falling back to a Canvas2D path otherwise.

    Examples:
        ```python
        from wigglystuff import AttractorWidget

        w = AttractorWidget(
            x_expr="sin(a*y) + c*cos(a*x)",
            y_expr="sin(b*x) + d*cos(b*y)",
            params={"a": -1.7, "b": 1.8, "c": -1.9, "d": -0.4},
        )
        w
        ```

        Or use a built-in preset:

        ```python
        w = AttractorWidget.clifford()
        w.params = {"a": -1.4, "b": 1.6, "c": 1.0, "d": 0.7}
        ```
    """

    _esm = Path(__file__).parent / "static" / "attractor.js"

    x_expr = traitlets.Unicode("sin(a*y) + c*cos(a*x)").tag(sync=True)
    y_expr = traitlets.Unicode("sin(b*x) + d*cos(b*y)").tag(sync=True)
    params = traitlets.Dict(value_trait=traitlets.Float()).tag(sync=True)
    n_points = traitlets.Int(1_000_000).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(600).tag(sync=True)
    colormap = traitlets.Unicode("phase").tag(sync=True)
    color_speed = traitlets.Float(0.22).tag(sync=True)
    color_phase = traitlets.Float(180.0).tag(sync=True)
    background = traitlets.Unicode("black").tag(sync=True)
    iterations_per_frame = traitlets.Int(1).tag(sync=True)
    view = traitlets.Tuple(
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        traitlets.Float(),
        default_value=(-2.5, 2.5, -2.5, 2.5),
    ).tag(sync=True)

    def __init__(
        self,
        x_expr: str = "sin(a*y) + c*cos(a*x)",
        y_expr: str = "sin(b*x) + d*cos(b*y)",
        params: Optional[dict[str, float]] = None,
        n_points: int = 1_000_000,
        width: int = 600,
        height: int = 600,
        colormap: str = "phase",
        color_speed: float = 0.22,
        color_phase: float = 180.0,
        background: str = "black",
        iterations_per_frame: int = 1,
        view: tuple[float, float, float, float] = (-2.5, 2.5, -2.5, 2.5),
        **kwargs: Any,
    ) -> None:
        """Create an AttractorWidget.

        Args:
            x_expr: Expression for the next x value, in terms of `x`, `y`, and
                any named parameters.
            y_expr: Expression for the next y value.
            params: Named scalar parameters referenced by the expressions.
            n_points: Number of trajectory points (clamped to [1_000, 1_500_000]).
            width: Canvas width in pixels.
            height: Canvas height in pixels.
            colormap: ``"phase"`` (default) uses Ricky Reusser's
                per-iteration-distance phase coloring. ``"magma"``,
                ``"viridis"``, ``"inferno"``, ``"plasma"``, or
                ``"grayscale"`` use a density-only LUT in that palette.
                ``color_speed`` / ``color_phase`` only affect ``"phase"``
                mode.
            color_speed: How quickly hue cycles with per-iteration distance.
                Set to ``0.0`` for a single hue. ``"phase"`` mode only.
            color_phase: Hue offset in degrees. ``"phase"`` mode only.
            background: One of "black", "white".
            iterations_per_frame: Extra iteration passes per animation frame.
            view: (xmin, xmax, ymin, ymax) world-space bounds.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        params = dict(params) if params is not None else {"a": -1.7, "b": 1.8, "c": -1.9, "d": -0.4}
        param_names = set(params.keys())
        _validate_expr(x_expr, param_names, "x_expr")
        _validate_expr(y_expr, param_names, "y_expr")
        if colormap not in _ALLOWED_COLORMAPS:
            raise ValueError(
                f"colormap must be one of {sorted(_ALLOWED_COLORMAPS)}."
            )
        if background not in _ALLOWED_BACKGROUNDS:
            raise ValueError(
                f"background must be one of {sorted(_ALLOWED_BACKGROUNDS)}."
            )
        n_points = max(1_000, min(1_500_000, int(n_points)))
        if iterations_per_frame < 1:
            raise ValueError("iterations_per_frame must be >= 1.")
        xmin, xmax, ymin, ymax = view
        if xmin >= xmax or ymin >= ymax:
            raise ValueError("view bounds must satisfy xmin<xmax and ymin<ymax.")

        super().__init__(
            x_expr=x_expr,
            y_expr=y_expr,
            params={k: float(v) for k, v in params.items()},
            n_points=n_points,
            width=width,
            height=height,
            colormap=colormap,
            color_speed=float(color_speed),
            color_phase=float(color_phase),
            background=background,
            iterations_per_frame=iterations_per_frame,
            view=view,
            **kwargs,
        )

    @traitlets.validate("x_expr")
    def _valid_x_expr(self, proposal: dict[str, Any]) -> str:
        _validate_expr(proposal["value"], set(self.params.keys()), "x_expr")
        return proposal["value"]

    @traitlets.validate("y_expr")
    def _valid_y_expr(self, proposal: dict[str, Any]) -> str:
        _validate_expr(proposal["value"], set(self.params.keys()), "y_expr")
        return proposal["value"]

    @traitlets.validate("params")
    def _valid_params(self, proposal: dict[str, Any]) -> dict[str, float]:
        value = proposal["value"]
        if not isinstance(value, dict):
            raise traitlets.TraitError("params must be a dict.")
        coerced = {}
        for k, v in value.items():
            if not isinstance(k, str) or not _IDENT_RE.fullmatch(k):
                raise traitlets.TraitError(
                    f"params key '{k}' is not a valid identifier."
                )
            if k in _ALLOWED_FUNCS or k in _ALLOWED_CONSTS or k in _ALLOWED_VARS:
                raise traitlets.TraitError(
                    f"params key '{k}' collides with a reserved name."
                )
            coerced[k] = float(v)
        return coerced

    @traitlets.validate("n_points")
    def _valid_n_points(self, proposal: dict[str, Any]) -> int:
        return max(1_000, min(1_500_000, int(proposal["value"])))

    @traitlets.validate("colormap")
    def _valid_colormap(self, proposal: dict[str, Any]) -> str:
        if proposal["value"] not in _ALLOWED_COLORMAPS:
            raise traitlets.TraitError(
                f"colormap must be one of {sorted(_ALLOWED_COLORMAPS)}."
            )
        return proposal["value"]

    @traitlets.validate("background")
    def _valid_background(self, proposal: dict[str, Any]) -> str:
        if proposal["value"] not in _ALLOWED_BACKGROUNDS:
            raise traitlets.TraitError(
                f"background must be one of {sorted(_ALLOWED_BACKGROUNDS)}."
            )
        return proposal["value"]

    @classmethod
    def clifford(
        cls,
        a: float = -1.7,
        b: float = 1.8,
        c: float = -1.9,
        d: float = -0.4,
        **kwargs: Any,
    ) -> "AttractorWidget":
        """Create an AttractorWidget pre-wired for the Clifford attractor."""
        return cls(
            x_expr="sin(a*y) + c*cos(a*x)",
            y_expr="sin(b*x) + d*cos(b*y)",
            params={"a": a, "b": b, "c": c, "d": d},
            **kwargs,
        )

    @classmethod
    def de_jong(
        cls,
        a: float = 2.01,
        b: float = -2.53,
        c: float = 1.61,
        d: float = -0.33,
        **kwargs: Any,
    ) -> "AttractorWidget":
        """Create an AttractorWidget pre-wired for the De Jong attractor."""
        return cls(
            x_expr="sin(a*y) - cos(b*x)",
            y_expr="sin(c*x) - cos(d*y)",
            params={"a": a, "b": b, "c": c, "d": d},
            view=(-2.2, 2.2, -2.2, 2.2),
            **kwargs,
        )
