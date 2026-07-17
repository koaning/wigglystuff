"""Interactive cube for progressively locking three dimensions."""

from math import isfinite
from numbers import Real
from pathlib import Path
from typing import Any

import anywidget
import traitlets


_ESM_PATH = Path(__file__).parent / "static" / "cube-widget.js"
_CSS_PATH = Path(__file__).parent / "static" / "cube-widget.css"

_DEFAULT_AXIS_VALUES = [0, 0.25, 0.5, 0.75, 1]
_AXIS_KEYS = ("x", "y", "z")


def _axis_default(name: str) -> dict[str, Any]:
    return {"name": name, "values": list(_DEFAULT_AXIS_VALUES)}


def _is_finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and isfinite(float(value))
    )


def _normalize_number(value: Real) -> int | float:
    return value if type(value) is int else float(value)


def _axis_midpoint(config: dict[str, Any]) -> int | float:
    values = config["values"]
    return values[len(values) // 2]


def _value_in_axis_range(value: Real, config: dict[str, Any]) -> bool:
    return min(config["values"]) <= value <= max(config["values"])


def _validate_axis_config(axis_key: str, config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ValueError(f"{axis_key}_axis must be a dictionary.")

    name = config.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(
            f"{axis_key}_axis must contain a non-empty string 'name'."
        )

    values = config.get("values")
    if not isinstance(values, (list, tuple)) or len(values) < 2:
        raise ValueError(
            f"{axis_key}_axis must contain at least two numeric values."
        )
    if any(not _is_finite_number(value) for value in values):
        raise ValueError(f"{axis_key}_axis values must be finite numbers.")
    if min(values) == max(values):
        raise ValueError(f"{axis_key}_axis values must have a non-zero range.")

    return {
        "name": name,
        "values": [_normalize_number(value) for value in values],
    }


class CubeWidget(anywidget.AnyWidget):
    """Select a plane, line, and point by progressively locking cube axes.

    Clicking an axis locks it and reveals a slider for its value. The first
    locked axis selects a plane, the second selects a line, and the third
    selects a point. Lock order is exposed so downstream code can preserve the
    same progressive slicing semantics.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import CubeWidget

        cube = mo.ui.anywidget(
            CubeWidget(
                x_axis={"name": "Angle", "values": [0, 45, 90]},
                y_axis={"name": "Force", "values": [0, 50, 100]},
                z_axis={"name": "Time", "values": [0, 1, 2]},
            )
        )
        cube
        ```

    Args:
        x_axis: X-axis configuration with a display ``name`` and numeric
            ``values`` defining its range.
        y_axis: Y-axis configuration with a display ``name`` and numeric
            ``values`` defining its range.
        z_axis: Z-axis configuration with a display ``name`` and numeric
            ``values`` defining its range.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    x_axis = traitlets.Dict(default_value=_axis_default("X")).tag(sync=True)
    y_axis = traitlets.Dict(default_value=_axis_default("Y")).tag(sync=True)
    z_axis = traitlets.Dict(default_value=_axis_default("Z")).tag(sync=True)

    locked_order = traitlets.List(
        traitlets.Unicode(), default_value=[]
    ).tag(sync=True)
    axis_values = traitlets.Dict(
        default_value={"x": 0.5, "y": 0.5, "z": 0.5}
    ).tag(sync=True)

    plane = traitlets.Dict(allow_none=True, default_value=None).tag(sync=True)
    line = traitlets.Dict(allow_none=True, default_value=None).tag(sync=True)
    point = traitlets.Dict(allow_none=True, default_value=None).tag(sync=True)

    def __init__(
        self,
        x_axis: dict[str, Any] | None = None,
        y_axis: dict[str, Any] | None = None,
        z_axis: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        supplied_axis_values = kwargs.pop("axis_values", None)
        self._initializing_axes = True
        try:
            super().__init__(
                x_axis=_axis_default("X") if x_axis is None else x_axis,
                y_axis=_axis_default("Y") if y_axis is None else y_axis,
                z_axis=_axis_default("Z") if z_axis is None else z_axis,
                **kwargs,
            )
        finally:
            self._initializing_axes = False

        initial_axis_values = {
            axis_key: _axis_midpoint(self._get_axis_config(axis_key))
            for axis_key in _AXIS_KEYS
        }
        if supplied_axis_values is not None:
            if not isinstance(supplied_axis_values, dict):
                raise ValueError("axis_values must be a dictionary.")
            initial_axis_values.update(supplied_axis_values)
        self.axis_values = initial_axis_values

        self.observe(
            self._update_outputs,
            names=[
                "locked_order",
                "axis_values",
                "x_axis",
                "y_axis",
                "z_axis",
            ],
        )
        self._update_outputs()

    @traitlets.validate("x_axis", "y_axis", "z_axis")
    def _validate_axis(self, proposal: dict[str, Any]) -> dict[str, Any]:
        axis_key = proposal["trait"].name.removesuffix("_axis")
        config = _validate_axis_config(axis_key, proposal["value"])
        if not getattr(self, "_initializing_axes", False):
            current_value = self.axis_values.get(axis_key)
            if current_value is not None and not _value_in_axis_range(
                current_value, config
            ):
                raise ValueError(
                    f"current {axis_key} value {current_value} is outside "
                    f"the proposed {config['name']} axis range "
                    f"[{min(config['values'])}, {max(config['values'])}]."
                )
        return config

    @traitlets.validate("axis_values")
    def _validate_axis_values(
        self, proposal: dict[str, Any]
    ) -> dict[str, Any]:
        values = proposal["value"]
        unknown = set(values) - set(_AXIS_KEYS)
        if unknown:
            raise ValueError(
                f"axis_values contains unknown axes: {sorted(unknown)}."
            )

        normalized = dict(self.axis_values)
        for axis_key, value in values.items():
            if not _is_finite_number(value):
                raise ValueError(
                    f"axis_values[{axis_key!r}] must be a finite number."
                )
            config = self._get_axis_config(axis_key)
            if not _value_in_axis_range(value, config):
                raise ValueError(
                    f"axis_values[{axis_key!r}] must be within the "
                    f"{config['name']} axis range "
                    f"[{min(config['values'])}, {max(config['values'])}]."
                )
            normalized[axis_key] = _normalize_number(value)
        return normalized

    def _get_axis_config(self, axis_key: str) -> dict[str, Any]:
        return {
            "x": self.x_axis,
            "y": self.y_axis,
            "z": self.z_axis,
        }[axis_key]

    def _update_outputs(self, change: dict[str, Any] | None = None) -> None:
        del change
        locked = self.locked_order
        values = self.axis_values

        outputs: list[dict[str, Any] | None] = [None, None, None]
        for index, axis_key in enumerate(locked[:3]):
            config = self._get_axis_config(axis_key)
            outputs[index] = {
                "axis": config["name"],
                "value": values.get(axis_key),
            }

        self.plane, self.line, self.point = outputs

    def reset(self) -> None:
        """Return to the volume view by unlocking every axis."""
        self.locked_order = []

    def lock_axis(self, axis_key: str, value: Real | None = None) -> None:
        """Lock an axis, optionally assigning its current value."""
        self._require_axis_key(axis_key)
        if value is not None:
            if not _is_finite_number(value):
                raise ValueError("value must be a finite number.")
            config = self._get_axis_config(axis_key)
            low = min(config["values"])
            high = max(config["values"])
            if not _value_in_axis_range(value, config):
                raise ValueError(
                    f"value must be within the {config['name']} axis range "
                    f"[{low}, {high}]."
                )
        if axis_key not in self.locked_order:
            self.locked_order = [*self.locked_order, axis_key]
        if value is not None:
            self.axis_values = {**self.axis_values, axis_key: value}

    def unlock_axis(self, axis_key: str) -> None:
        """Unlock an axis while preserving the order of the remaining axes."""
        self._require_axis_key(axis_key)
        if axis_key in self.locked_order:
            self.locked_order = [
                key for key in self.locked_order if key != axis_key
            ]

    @staticmethod
    def _require_axis_key(axis_key: str) -> None:
        if axis_key not in _AXIS_KEYS:
            raise ValueError("axis_key must be 'x', 'y', or 'z'")
