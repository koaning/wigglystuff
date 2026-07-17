"""Tests for the CubeWidget dimension-locking widget."""

import math
import json
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
    assert cube.locked_order == []
    assert cube.axis_values == {"x": 0.5, "y": 0.5, "z": 0.5}
    assert cube.plane is None
    assert cube.line is None
    assert cube.point is None


def test_custom_axis_configs_are_preserved():
    cube = CubeWidget(
        x_axis={"name": "Angle", "values": [0, 45, 90]},
        y_axis={"name": "Force", "values": [0, 50, 100]},
        z_axis={"name": "Time", "values": [0, 1, 2]},
    )

    assert cube.x_axis == {"name": "Angle", "values": [0, 45, 90]}
    assert cube.y_axis == {"name": "Force", "values": [0, 50, 100]}
    assert cube.z_axis == {"name": "Time", "values": [0, 1, 2]}
    assert cube.axis_values == {"x": 45, "y": 50, "z": 1}


def test_custom_axis_defaults_to_configured_middle_entry():
    cube = CubeWidget(
        x_axis={"name": "Offset", "values": [10, 20]},
    )

    cube.lock_axis("x")

    assert cube.axis_values["x"] == 20
    assert cube.plane == {"axis": "Offset", "value": 20}


def test_explicit_initial_axis_values_are_preserved():
    cube = CubeWidget(
        x_axis={"name": "Angle", "values": [0, 45, 90]},
        axis_values={"x": 30, "y": 0.25, "z": 0.75},
    )

    assert cube.axis_values == {"x": 30, "y": 0.25, "z": 0.75}


def test_initial_axis_values_must_be_in_configured_range():
    with pytest.raises(ValueError, match=r"axis_values\['x'\] must be within"):
        CubeWidget(
            x_axis={"name": "Offset", "values": [10, 20]},
            axis_values={"x": 0.5},
        )


def test_numeric_state_is_normalized_for_json_sync():
    cube = CubeWidget(
        x_axis={"name": "Ratio", "values": [Fraction(0), Fraction(1)]}
    )
    cube.lock_axis("x", Fraction(1, 2))

    assert cube.x_axis["values"] == [0.0, 1.0]
    assert [type(value) for value in cube.x_axis["values"]] == [float, float]
    assert cube.axis_values["x"] == 0.5
    json.dumps(cube.get_state())


@pytest.mark.parametrize(
    "config, message",
    [
        ({"values": [0, 1]}, "non-empty string 'name'"),
        ({"name": "", "values": [0, 1]}, "non-empty string 'name'"),
        ({"name": "X"}, "at least two numeric values"),
        ({"name": "X", "values": [0]}, "at least two numeric values"),
        ({"name": "X", "values": [0, "one"]}, "finite numbers"),
        ({"name": "X", "values": [0, math.inf]}, "finite numbers"),
        ({"name": "X", "values": [1, 1]}, "non-zero range"),
    ],
)
def test_invalid_axis_configs_raise(config, message):
    with pytest.raises(ValueError, match=message):
        CubeWidget(x_axis=config)


def test_locking_axes_updates_plane_line_and_point_in_order():
    cube = CubeWidget(
        x_axis={"name": "Angle", "values": [0, 45, 90]},
        y_axis={"name": "Force", "values": [0, 50, 100]},
        z_axis={"name": "Time", "values": [0, 1, 2]},
    )

    cube.lock_axis("y", 75)
    assert cube.locked_order == ["y"]
    assert cube.plane == {"axis": "Force", "value": 75}
    assert cube.line is None
    assert cube.point is None

    cube.lock_axis("x", 30)
    assert cube.locked_order == ["y", "x"]
    assert cube.plane == {"axis": "Force", "value": 75}
    assert cube.line == {"axis": "Angle", "value": 30}
    assert cube.point is None

    cube.lock_axis("z", 1.5)
    assert cube.locked_order == ["y", "x", "z"]
    assert cube.point == {"axis": "Time", "value": 1.5}


def test_locking_an_axis_twice_does_not_duplicate_it():
    cube = CubeWidget()

    cube.lock_axis("x")
    cube.lock_axis("x", 0.75)

    assert cube.locked_order == ["x"]
    assert cube.axis_values["x"] == 0.75
    assert cube.plane == {"axis": "X", "value": 0.75}


@pytest.mark.parametrize("value", [True, "bad", math.inf, math.nan])
def test_lock_axis_rejects_non_finite_numeric_values(value):
    cube = CubeWidget()

    with pytest.raises(ValueError, match="value must be a finite number"):
        cube.lock_axis("x", value)

    assert cube.locked_order == []


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_lock_axis_rejects_values_outside_axis_range(value):
    cube = CubeWidget()

    with pytest.raises(ValueError, match="value must be within the X axis range"):
        cube.lock_axis("x", value)

    assert cube.locked_order == []


def test_axis_values_reject_non_numeric_state():
    cube = CubeWidget()

    with pytest.raises(
        ValueError,
        match=r"axis_values\['x'\] must be a finite number",
    ):
        cube.axis_values = {"x": "bad", "y": 0.5, "z": 0.5}


def test_axis_values_reject_out_of_range_state():
    cube = CubeWidget()

    with pytest.raises(ValueError, match=r"axis_values\['x'\] must be within"):
        cube.axis_values = {"x": 999}

    assert cube.axis_values["x"] == 0.5


def test_axis_config_rejects_range_that_excludes_current_value():
    cube = CubeWidget()

    with pytest.raises(ValueError, match="current x value 0.5 is outside"):
        cube.x_axis = {"name": "Offset", "values": [10, 20]}

    assert cube.x_axis["values"] == [0, 0.25, 0.5, 0.75, 1]


def test_unlocking_recomputes_outputs_from_remaining_order():
    cube = CubeWidget()
    cube.lock_axis("x", 0.25)
    cube.lock_axis("y", 0.75)
    cube.lock_axis("z", 1)

    cube.unlock_axis("x")

    assert cube.locked_order == ["y", "z"]
    assert cube.plane == {"axis": "Y", "value": 0.75}
    assert cube.line == {"axis": "Z", "value": 1}
    assert cube.point is None


def test_reset_unlocks_every_axis_but_keeps_values():
    cube = CubeWidget()
    cube.lock_axis("x", 0.25)
    cube.lock_axis("y", 0.75)

    cube.reset()

    assert cube.locked_order == []
    assert cube.axis_values == {"x": 0.25, "y": 0.75, "z": 0.5}
    assert cube.plane is None
    assert cube.line is None
    assert cube.point is None


@pytest.mark.parametrize("method", ["lock_axis", "unlock_axis"])
def test_helpers_reject_unknown_axis_keys(method):
    cube = CubeWidget()

    with pytest.raises(ValueError, match="axis_key must be 'x', 'y', or 'z'"):
        getattr(cube, method)("q")


def test_initial_locked_state_computes_outputs():
    cube = CubeWidget(
        locked_order=["z"],
        axis_values={"x": 0.1, "y": 0.2, "z": 0.3},
    )

    assert cube.plane == {"axis": "Z", "value": 0.3}
