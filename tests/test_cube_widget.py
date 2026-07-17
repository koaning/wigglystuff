"""Focused tests for CubeWidget's public Python behavior."""

import json
import math
from fractions import Fraction

import pytest

from wigglystuff import CubeWidget


def test_defaults():
    cube = CubeWidget()

    assert cube.x_axis == {
        "name": "X",
        "values": [0, 0.25, 0.5, 0.75, 1],
    }
    assert cube.y_axis["name"] == "Y"
    assert cube.z_axis["name"] == "Z"
    assert cube.axis_values == {"x": 0.5, "y": 0.5, "z": 0.5}
    assert cube.locked_order == []
    assert cube.plane is cube.line is cube.point is None


def test_custom_axes_and_initial_values():
    cube = CubeWidget(
        x_axis={"name": "Angle", "values": [0, 45, 90]},
        y_axis={"name": "Force", "values": [0, 50, 100]},
        z_axis={"name": "Time", "values": [0, 1, 2]},
        axis_values={"x": 30},
    )

    assert cube.x_axis == {"name": "Angle", "values": [0, 45, 90]}
    assert cube.y_axis == {"name": "Force", "values": [0, 50, 100]}
    assert cube.z_axis == {"name": "Time", "values": [0, 1, 2]}
    assert cube.axis_values == {"x": 30, "y": 50, "z": 1}


def test_invalid_axis_configs():
    cases = [
        ({"values": [0, 1]}, "non-empty string 'name'"),
        ({"name": "", "values": [0, 1]}, "non-empty string 'name'"),
        ({"name": "X"}, "at least two numeric values"),
        ({"name": "X", "values": [0]}, "at least two numeric values"),
        ({"name": "X", "values": [0, "one"]}, "finite numbers"),
        ({"name": "X", "values": [0, math.inf]}, "finite numbers"),
        ({"name": "X", "values": [1, 1]}, "non-zero range"),
    ]

    for config, message in cases:
        with pytest.raises(ValueError, match=message):
            CubeWidget(x_axis=config)


def test_axis_value_state_validation():
    with pytest.raises(ValueError, match=r"axis_values\['x'\] must be within"):
        CubeWidget(
            x_axis={"name": "Offset", "values": [10, 20]},
            axis_values={"x": 0.5},
        )

    cube = CubeWidget()
    for value, message in [
        ("bad", "must be a finite number"),
        (999, "must be within"),
    ]:
        with pytest.raises(ValueError, match=message):
            cube.axis_values = {"x": value}

    with pytest.raises(ValueError, match="current x value 0.5 is outside"):
        cube.x_axis = {"name": "Offset", "values": [10, 20]}


def test_numeric_state_is_json_safe():
    cube = CubeWidget(
        x_axis={"name": "Ratio", "values": [Fraction(0), Fraction(1)]}
    )
    cube.lock_axis("x", Fraction(1, 2))

    assert cube.x_axis["values"] == [0.0, 1.0]
    assert cube.axis_values["x"] == 0.5
    json.dumps(cube.get_state())


def test_locking_axes_derives_plane_line_and_point_in_order():
    cube = CubeWidget(
        x_axis={"name": "Angle", "values": [0, 45, 90]},
        y_axis={"name": "Force", "values": [0, 50, 100]},
        z_axis={"name": "Time", "values": [0, 1, 2]},
    )

    cube.lock_axis("y", 75)
    assert cube.plane == {"axis": "Force", "value": 75}
    assert cube.line is cube.point is None

    cube.lock_axis("x", 30)
    assert cube.line == {"axis": "Angle", "value": 30}
    assert cube.point is None

    cube.lock_axis("z", 1.5)
    assert cube.locked_order == ["y", "x", "z"]
    assert cube.point == {"axis": "Time", "value": 1.5}


def test_locking_is_idempotent_and_initial_locks_are_derived():
    cube = CubeWidget()
    cube.lock_axis("x")
    cube.lock_axis("x", 0.75)

    assert cube.locked_order == ["x"]
    assert cube.plane == {"axis": "X", "value": 0.75}

    initial = CubeWidget(
        locked_order=["z"],
        axis_values={"x": 0.1, "y": 0.2, "z": 0.3},
    )
    assert initial.plane == {"axis": "Z", "value": 0.3}


def test_invalid_synced_lock_state():
    for locked_order, message in [
        (["q"], "unknown axes"),
        (["x", "x"], "must not contain duplicates"),
    ]:
        with pytest.raises(ValueError, match=message):
            CubeWidget(locked_order=locked_order)


def test_lock_axis_rejects_invalid_values():
    cube = CubeWidget()

    for value in [True, "bad", math.inf, math.nan]:
        with pytest.raises(ValueError, match="value must be a finite number"):
            cube.lock_axis("x", value)

    for value in [-0.1, 1.1]:
        with pytest.raises(ValueError, match="must be within the X axis range"):
            cube.lock_axis("x", value)

    assert cube.locked_order == []


def test_unlock_recomputes_outputs():
    cube = CubeWidget()
    cube.lock_axis("x", 0.25)
    cube.lock_axis("y", 0.75)
    cube.lock_axis("z", 1)

    cube.unlock_axis("x")

    assert cube.locked_order == ["y", "z"]
    assert cube.plane == {"axis": "Y", "value": 0.75}
    assert cube.line == {"axis": "Z", "value": 1}
    assert cube.point is None


def test_reset_keeps_values_and_clears_outputs():
    cube = CubeWidget()
    cube.lock_axis("x", 0.25)
    cube.lock_axis("y", 0.75)

    cube.reset()

    assert cube.locked_order == []
    assert cube.axis_values == {"x": 0.25, "y": 0.75, "z": 0.5}
    assert cube.plane is cube.line is cube.point is None


def test_helpers_reject_unknown_axis_keys():
    cube = CubeWidget()

    for method in [cube.lock_axis, cube.unlock_axis]:
        with pytest.raises(ValueError, match="axis_key must be 'x', 'y', or 'z'"):
            method("q")
