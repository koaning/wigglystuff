"""Interactive KaTeX formulas with draggable named parameters."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "latex-tangle.js"
_CSS_PATH = Path(__file__).parent / "static" / "latex-tangle.css"
_MARKER_RE = re.compile(r"\\tangle\{([A-Za-z][A-Za-z0-9_-]*)\}")
_DEFAULT_COLORS = (
    {"light": "#246bce", "dark": "#75a7ff"},
    {"light": "#b45b1b", "dark": "#ffad66"},
    {"light": "#147a68", "dark": "#5ed5bd"},
    {"light": "#a23b78", "dark": "#f08bc2"},
    {"light": "#6f5cbd", "dark": "#b9a8ff"},
)


def _finite_float(value: Any, *, name: str, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"parameter {name!r} {field} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"parameter {name!r} {field} must be a finite number."
        ) from exc
    if not math.isfinite(result):
        raise ValueError(f"parameter {name!r} {field} must be a finite number.")
    return result


def _positive_int(value: Any, *, name: str, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"parameter {name!r} {field} must be a positive integer.")
    return value


def _normalize_color(value: Any, *, name: str, index: int) -> dict[str, str]:
    if value is None:
        return dict(_DEFAULT_COLORS[index % len(_DEFAULT_COLORS)])
    if isinstance(value, str) and value:
        return {"light": value, "dark": value}
    if isinstance(value, Mapping):
        if set(value) != {"light", "dark"}:
            raise ValueError(
                f"parameter {name!r} color mapping must contain 'light' and 'dark'."
            )
        light = value["light"]
        dark = value["dark"]
        if not isinstance(light, str) or not light or not isinstance(dark, str) or not dark:
            raise ValueError(
                f"parameter {name!r} color mapping must contain non-empty strings."
            )
        return {"light": light, "dark": dark}
    raise ValueError(
        f"parameter {name!r} color must be a CSS color string or a light/dark mapping."
    )


def _normalize_parameters(
    parameters: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters must be a mapping of names to configuration dictionaries.")

    normalized: dict[str, dict[str, Any]] = {}
    for index, (name, raw) in enumerate(parameters.items()):
        if not isinstance(name, str) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]*", name
        ):
            raise ValueError(
                "parameter names must start with a letter and contain only letters, "
                "numbers, underscores, or hyphens."
            )
        if not isinstance(raw, Mapping):
            raise ValueError(f"parameter {name!r} configuration must be a mapping.")

        value = _finite_float(raw.get("value"), name=name, field="value")
        min_value = _finite_float(
            raw.get("min_value", -100), name=name, field="min_value"
        )
        max_value = _finite_float(
            raw.get("max_value", 100), name=name, field="max_value"
        )
        step = _finite_float(raw.get("step", 1), name=name, field="step")
        if min_value >= max_value:
            raise ValueError(f"parameter {name!r} min_value must be less than max_value.")
        if step <= 0:
            raise ValueError(f"parameter {name!r} step must be positive.")
        if not min_value <= value <= max_value:
            raise ValueError(
                f"parameter {name!r} value must be between min_value and max_value."
            )

        digits = raw.get("digits", 1)
        if isinstance(digits, bool) or not isinstance(digits, int) or digits < 0:
            raise ValueError(
                f"parameter {name!r} digits must be a non-negative integer."
            )
        pixels_per_step = _positive_int(
            raw.get("pixels_per_step", 7), name=name, field="pixels_per_step"
        )
        display = raw.get("display", "number")
        if display not in {"number", "symbol"}:
            raise ValueError(
                f"parameter {name!r} display must be 'number' or 'symbol'."
            )
        symbol = raw.get("symbol", name)
        label = raw.get("label", f"parameter {name}")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError(f"parameter {name!r} symbol must be a non-empty string.")
        if not isinstance(label, str) or not label:
            raise ValueError(f"parameter {name!r} label must be a non-empty string.")

        normalized[name] = {
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "step": step,
            "digits": digits,
            "display": display,
            "symbol": symbol,
            "label": label,
            "pixels_per_step": pixels_per_step,
            "color": _normalize_color(raw.get("color"), name=name, index=index),
        }
    return normalized


class TangleLatex(anywidget.AnyWidget):
    """Render a KaTeX formula with draggable named numeric parameters.

    Put ``\\tangle{name}`` markers in ``latex`` and configure each name in
    ``parameters``. A parameter can display its formatted number directly or
    remain symbolic until it is dragged or edited. Repeated markers share one
    value and update together.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import TangleLatex

        formula = mo.ui.anywidget(
            TangleLatex(
                latex=r"f(x) = \tangle{a}x^2 + \tangle{b}x + \tangle{a}",
                parameters={
                    "a": {
                        "value": 2.5,
                        "min_value": -5,
                        "max_value": 5,
                        "step": 0.1,
                        "display": "symbol",
                    },
                    "b": {
                        "value": 1,
                        "min_value": -10,
                        "max_value": 10,
                        "step": 0.5,
                        "display": "symbol",
                    },
                },
                reveal_all_on_drag=True,
            )
        )
        formula
        ```
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    latex = traitlets.Unicode().tag(sync=True)
    parameters = traitlets.Dict(default_value={}).tag(sync=True)
    values = traitlets.Dict(default_value={}).tag(sync=True)
    display_mode = traitlets.Bool(True).tag(sync=True)
    editor = traitlets.Enum(["popover", "inline"], default_value="popover").tag(
        sync=True
    )
    reveal_all_on_drag = traitlets.Bool(False).tag(sync=True)
    theme = traitlets.Enum(["auto", "light", "dark"], default_value="auto").tag(
        sync=True
    )
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        latex: str,
        parameters: Mapping[str, Mapping[str, Any]],
        *,
        display_mode: bool = True,
        editor: str = "popover",
        reveal_all_on_drag: bool = False,
        theme: str = "auto",
        **kwargs: Any,
    ) -> None:
        """Create a TangleLatex widget.

        Args:
            latex: KaTeX source containing one or more ``\\tangle{name}`` markers.
            parameters: Mapping from marker name to its numeric configuration.
                ``value`` is required. Optional keys are ``min_value``,
                ``max_value``, ``step``, ``digits``, ``display`` (``"number"``
                or ``"symbol"``), ``symbol``, ``label``, ``pixels_per_step``,
                and ``color`` (a CSS string or ``{"light": ..., "dark": ...}``).
            display_mode: Render using KaTeX display mode.
            editor: Numeric click editor style: ``"popover"`` or ``"inline"``.
            reveal_all_on_drag: Reveal every symbolic parameter as a number while
                any parameter is actively dragged. When false, reveal only the
                selected parameter.
            theme: Color theme: ``"auto"``, ``"light"``, or ``"dark"``.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if not isinstance(latex, str):
            raise ValueError("latex must be a string.")
        if editor not in {"popover", "inline"}:
            raise ValueError("editor must be 'popover' or 'inline'.")
        if theme not in {"auto", "light", "dark"}:
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")

        marker_names = set(_MARKER_RE.findall(latex))
        if not marker_names:
            raise ValueError("latex must contain at least one \\tangle{name} marker.")
        normalized = _normalize_parameters(parameters)
        configured_names = set(normalized)
        missing = sorted(marker_names - configured_names)
        unused = sorted(configured_names - marker_names)
        if missing:
            raise ValueError(
                "missing configuration for parameter marker(s): " + ", ".join(missing)
            )
        if unused:
            raise ValueError(
                "parameter configuration not referenced by latex: " + ", ".join(unused)
            )

        values = {name: spec["value"] for name, spec in normalized.items()}
        super().__init__(
            latex=latex,
            parameters=normalized,
            values=values,
            display_mode=display_mode,
            editor=editor,
            reveal_all_on_drag=reveal_all_on_drag,
            theme=theme,
            **kwargs,
        )
