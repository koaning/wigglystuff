"""Turn a typed Python function into a draggable/clickable call expression.

``TangleFunction`` introspects a function's signature and renders it as a clean
call expression, e.g. ``train(lr=0.01, epochs=10, optimizer='adam')``. Numeric
arguments drag-scrub, arguments with a known set of options (``Literal``,
``Enum``, ``bool``) click-cycle, and string arguments are click-to-edit. The
current arguments are synced back to Python as a plain ``values`` dict so you can
splat them straight into the function::

    fn(**tf.value["values"])
"""

from __future__ import annotations

import enum
import inspect
import math
import typing
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Optional

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "tangle-function.js"
_CSS_PATH = Path(__file__).parent / "static" / "tangle-function.css"

_SKIP_KINDS = {
    inspect.Parameter.VAR_POSITIONAL,
    inspect.Parameter.VAR_KEYWORD,
}
_BOUND_KEYS = ("min_value", "max_value", "step", "digits", "pixels_per_step")


def _label_for(value: Any) -> str:
    """Source-like display label for a choice/string value ('red', True, 3)."""
    return repr(value)


def _decimals(value: float) -> int:
    """Number of significant decimal places in ``value`` (0.001 -> 3, 10 -> 0)."""
    value = abs(float(value))
    if value == 0:
        return 0
    text = f"{value:.12f}".rstrip("0")
    if "." not in text:
        return 0
    return min(8, len(text.split(".")[1]))


def _unwrap(hint: Any) -> tuple[Any, list[Any]]:
    """Strip ``Annotated[...]`` and single-type ``Optional[...]`` wrappers.

    Returns the underlying type plus any ``Annotated`` metadata objects.
    """
    metadata: list[Any] = []
    if hasattr(hint, "__metadata__"):
        metadata.extend(hint.__metadata__)
        hint = hint.__origin__
    if typing.get_origin(hint) is typing.Union:
        args = [a for a in typing.get_args(hint) if a is not type(None)]
        if len(args) == 1:
            hint = args[0]
            if hasattr(hint, "__metadata__"):
                metadata.extend(hint.__metadata__)
                hint = hint.__origin__
    return hint, metadata


def _apply_constraints(cfg: dict[str, Any], metadata: list[Any]) -> None:
    """Fold ``Annotated`` metadata into a numeric config dict.

    Recognizes (by duck-typing, so no import is required):
    - plain ``Mapping`` metadata (e.g. ``{"min_value": 0, "step": 0.1}``),
    - ``annotated_types`` constraints ``Ge/Gt/Le/Lt/Interval/MultipleOf``,
    - ``pydantic.Field(...)``, whose ``FieldInfo`` carries the same constraints
      in a nested ``.metadata`` list.
    Anything unrecognized is ignored. Existing keys are not overwritten, so an
    explicit ``params=`` override (applied later) always wins.
    """
    for meta in metadata:
        if isinstance(meta, Mapping):
            for key, value in meta.items():
                cfg.setdefault(key, value)
            continue
        nested = getattr(meta, "metadata", None)
        if isinstance(nested, (list, tuple)):
            _apply_constraints(cfg, list(nested))
        for attr, key in (
            ("ge", "min_value"),
            ("gt", "min_value"),
            ("le", "max_value"),
            ("lt", "max_value"),
            ("multiple_of", "step"),
        ):
            value = getattr(meta, attr, None)
            if value is not None:
                cfg.setdefault(key, value)


def _is_literal(hint: Any) -> bool:
    return typing.get_origin(hint) is typing.Literal


def _is_enum(hint: Any) -> bool:
    return isinstance(hint, type) and issubclass(hint, enum.Enum)


def _choice_spec(
    name: str,
    options: list[Any],
    current: Any,
    *,
    labels: Optional[list[str]] = None,
) -> dict[str, Any]:
    if len(options) < 1:
        raise ValueError(f"parameter {name!r} must have at least one option.")
    if current not in options:
        current = options[0]
    if labels is None:
        labels = [_label_for(option) for option in options]
    return {
        "kind": "choice",
        "options": options,
        "option_labels": labels,
        "value": current,
        "label": name,
    }


def _number_spec(
    name: str,
    default: Optional[float],
    is_int: bool,
    override: Mapping[str, Any],
    metadata: list[Any],
) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    _apply_constraints(cfg, metadata)
    cfg.update({k: override[k] for k in _BOUND_KEYS if k in override})

    value = float(override["value"]) if "value" in override else float(default or 0.0)
    if not math.isfinite(value):
        raise ValueError(f"parameter {name!r} value must be a finite number.")

    # Numbers are unbounded scrubbers by default; only clamp when the user
    # explicitly supplies a bound (via params= or Annotated metadata).
    min_value = float(cfg["min_value"]) if "min_value" in cfg else None
    max_value = float(cfg["max_value"]) if "max_value" in cfg else None
    step = float(cfg.get("step", 1.0 if is_int else 0.1))
    default_digits = 0 if is_int else max(_decimals(step), _decimals(value))
    digits = int(cfg.get("digits", default_digits))
    pixels_per_step = int(cfg.get("pixels_per_step", 7))

    if step <= 0:
        raise ValueError(f"parameter {name!r} step must be positive.")
    if digits < 0:
        raise ValueError(f"parameter {name!r} digits must be non-negative.")
    if pixels_per_step <= 0:
        raise ValueError(f"parameter {name!r} pixels_per_step must be positive.")
    if min_value is not None and max_value is not None and min_value >= max_value:
        raise ValueError(f"parameter {name!r} min_value must be less than max_value.")
    if min_value is not None and value < min_value:
        raise ValueError(f"parameter {name!r} value is below min_value.")
    if max_value is not None and value > max_value:
        raise ValueError(f"parameter {name!r} value is above max_value.")

    return {
        "kind": "number",
        "value": int(round(value)) if is_int else value,
        "min_value": min_value,
        "max_value": max_value,
        "step": step,
        "digits": digits,
        "pixels_per_step": pixels_per_step,
        "is_int": is_int,
        "label": name,
    }


def _classify(
    name: str,
    param: inspect.Parameter,
    hint: Any,
    override: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the normalized frontend spec for a single parameter."""
    has_default = param.default is not inspect.Parameter.empty
    default = param.default if has_default else None

    # An explicit options override turns any parameter into a click-cycle choice.
    if "options" in override:
        options = list(override["options"])
        current = override.get("value", default if has_default else None)
        return _choice_spec(name, options, current)

    base, metadata = _unwrap(hint)

    if _is_literal(base):
        options = list(typing.get_args(base))
        current = default if has_default else options[0]
        return _choice_spec(name, options, current)

    if _is_enum(base):
        members = list(base)
        options = [member.value for member in members]
        labels = [_label_for(member.value) for member in members]
        current = default.value if isinstance(default, enum.Enum) else options[0]
        return _choice_spec(name, options, current, labels=labels)

    if base is bool or isinstance(default, bool):
        return _choice_spec(name, [False, True], bool(default) if has_default else False)

    if base in (int, float) or (
        not isinstance(default, bool) and isinstance(default, (int, float))
    ):
        is_int = base is int or (base not in (int, float) and isinstance(default, int))
        return _number_spec(name, default, is_int, override, metadata)

    if base is str or isinstance(default, str):
        return {"kind": "string", "value": str(default) if has_default else "", "label": name}

    if has_default:
        # Last resort: show whatever it is as an editable string.
        return {"kind": "string", "value": str(default), "label": name}

    raise ValueError(
        f"parameter {name!r} has no type hint or default to infer a control from; "
        "annotate it (int/float/bool/str/Literal/Enum) or pass it in params=."
    )


class TangleFunction(anywidget.AnyWidget):
    """Render a typed Python function as an interactive call expression.

    Each argument becomes editable in place: numbers drag horizontally to scrub,
    ``Literal``/``Enum``/``bool`` arguments click to cycle through their known
    options, and strings are click-to-edit. The live arguments are synced to the
    ``values`` dict, ready to splat into the function.

    Examples:
        ```python
        import marimo as mo
        from typing import Literal
        from wigglystuff import TangleFunction

        def train(lr: float = 0.01, epochs: int = 10,
                  optimizer: Literal["adam", "sgd"] = "adam", shuffle: bool = True):
            ...

        tf = mo.ui.anywidget(TangleFunction(train))
        tf
        # in another cell:
        train(**tf.value["values"])
        ```

    Numbers are unbounded scrubbers by default. Give one a range or a step by
    annotating it with `annotated_types` constraints (the same ones pydantic
    uses, so ``pydantic.Field(ge=..., le=...)`` works too):

        ```python
        from typing import Annotated
        from annotated_types import Ge, Le, MultipleOf

        def generate(temperature: Annotated[float, Ge(0), Le(2), MultipleOf(0.05)] = 0.7):
            ...

        mo.ui.anywidget(TangleFunction(generate))
        ```

    Note:
        For ``Enum`` parameters the emitted value is the member's ``.value`` (so
        it stays JSON-serializable and matches the displayed label). ``Literal``
        is the recommended way to expose a known set of options.
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    fn_name = traitlets.Unicode("f").tag(sync=True)
    parameters = traitlets.Dict(default_value={}).tag(sync=True)
    param_order = traitlets.List(default_value=[]).tag(sync=True)
    values = traitlets.Dict(default_value={}).tag(sync=True)
    theme = traitlets.Enum(["auto", "light", "dark"], default_value="auto").tag(sync=True)
    width = traitlets.Int(560).tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(
        self,
        fn: Callable[..., Any],
        params: Optional[Mapping[str, Mapping[str, Any]]] = None,
        *,
        theme: str = "auto",
        width: int = 560,
        **kwargs: Any,
    ) -> None:
        """Create a TangleFunction widget.

        Args:
            fn: The function to render. Its parameters are introspected from type
                hints and defaults.
            params: Optional per-parameter overrides keyed by name. For numeric
                parameters: ``min_value``, ``max_value``, ``step``, ``digits``,
                ``pixels_per_step``, and ``value``. Any parameter may also be
                given ``options`` (a list) to force a click-cycle choice. These
                take precedence over ``annotated_types``/``pydantic.Field``
                constraints read from the parameter's ``Annotated`` metadata.
            theme: Color theme: ``"auto"``, ``"light"``, or ``"dark"``.
            width: Maximum width in pixels before the expression wraps.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if not callable(fn):
            raise ValueError("fn must be callable.")
        params = params or {}
        if not isinstance(params, Mapping):
            raise ValueError("params must be a mapping of parameter names to configs.")
        if theme not in {"auto", "light", "dark"}:
            raise ValueError("theme must be 'auto', 'light', or 'dark'.")

        try:
            sig = inspect.signature(fn)
        except (ValueError, TypeError) as exc:
            raise ValueError("fn must be an introspectable callable.") from exc
        try:
            hints = typing.get_type_hints(fn, include_extras=True)
        except Exception:
            hints = {}

        parameters: dict[str, dict[str, Any]] = {}
        param_order: list[str] = []
        for pname, param in sig.parameters.items():
            if pname == "self" or param.kind in _SKIP_KINDS:
                continue
            override = params.get(pname, {})
            if not isinstance(override, Mapping):
                raise ValueError(f"params[{pname!r}] must be a mapping.")
            hint = hints.get(pname, param.annotation)
            if hint is inspect.Parameter.empty:
                hint = None
            parameters[pname] = _classify(pname, param, hint, override)
            param_order.append(pname)

        unknown = sorted(set(params) - set(parameters))
        if unknown:
            raise ValueError(
                "params keys not found among the function's parameters: "
                + ", ".join(unknown)
            )

        values = {name: parameters[name]["value"] for name in param_order}
        super().__init__(
            fn_name=getattr(fn, "__name__", "f"),
            parameters=parameters,
            param_order=param_order,
            values=values,
            theme=theme,
            width=width,
            **kwargs,
        )
        self._fn = fn
