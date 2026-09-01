"""Tests for the TangleFunction widget."""

import enum
from dataclasses import dataclass
from typing import Annotated, Literal, Optional

import pytest

from wigglystuff import TangleFunction


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def _sample(
    lr: float = 0.01,
    epochs: int = 10,
    optimizer: Literal["adam", "sgd", "rmsprop"] = "adam",
    color: Color = Color.GREEN,
    shuffle: bool = True,
    name: str = "run-1",
):
    return locals()


def test_fn_name_order_and_values():
    tf = TangleFunction(_sample)
    assert tf.fn_name == "_sample"
    assert tf.param_order == ["lr", "epochs", "optimizer", "color", "shuffle", "name"]
    assert tf.values == {
        "lr": 0.01,
        "epochs": 10,
        "optimizer": "adam",
        "color": "green",  # Enum emits the member's .value
        "shuffle": True,
        "name": "run-1",
    }


def test_kind_classification():
    p = TangleFunction(_sample).parameters
    assert p["lr"]["kind"] == "number" and p["lr"]["is_int"] is False
    assert p["epochs"]["kind"] == "number" and p["epochs"]["is_int"] is True
    assert p["optimizer"]["kind"] == "choice"
    assert p["optimizer"]["options"] == ["adam", "sgd", "rmsprop"]
    assert p["color"]["kind"] == "choice"
    assert p["color"]["options"] == ["red", "green", "blue"]  # Enum .value list
    assert p["shuffle"]["kind"] == "choice"
    assert p["shuffle"]["options"] == [False, True]
    assert p["name"]["kind"] == "string"


def test_numbers_unbounded_by_default():
    p = TangleFunction(_sample).parameters
    assert p["lr"]["min_value"] is None and p["lr"]["max_value"] is None
    assert p["epochs"]["min_value"] is None and p["epochs"]["max_value"] is None


def test_digits_follow_step_and_value_precision():
    def f(a: float = 0.01, b: float = 3.0, n: int = 5):
        return a, b, n

    p = TangleFunction(f, params={"a": {"step": 0.001}}).parameters
    assert p["a"]["step"] == 0.001 and p["a"]["digits"] == 3
    assert p["b"]["digits"] == 1  # step 0.1
    assert p["n"]["digits"] == 0  # int


def test_params_override_bounds_value_and_options():
    def f(x: float = 0.5, mode="a"):
        return x, mode

    tf = TangleFunction(
        f,
        params={
            "x": {"min_value": 0.0, "max_value": 1.0, "step": 0.1, "value": 0.3},
            "mode": {"options": ["a", "b", "c"]},
        },
    )
    assert tf.parameters["x"]["min_value"] == 0.0
    assert tf.parameters["x"]["max_value"] == 1.0
    assert tf.values["x"] == 0.3
    assert tf.parameters["mode"]["kind"] == "choice"
    assert tf.parameters["mode"]["options"] == ["a", "b", "c"]


@dataclass
class _Ge:  # duck-typed stand-in for annotated_types.Ge (no dependency needed)
    ge: float


@dataclass
class _Le:
    le: float


@dataclass
class _MultipleOf:
    multiple_of: float


@dataclass
class _FieldInfo:  # duck-typed stand-in for pydantic's FieldInfo
    metadata: list


def test_annotated_types_constraints_become_bounds_and_step():
    def f(
        temp: Annotated[float, _Ge(0.0), _Le(2.0), _MultipleOf(0.05)] = 0.7,
        capped: Annotated[int, _FieldInfo(metadata=[_Ge(1), _Le(4096)])] = 256,
    ):
        return temp, capped

    p = TangleFunction(f).parameters
    assert p["temp"]["min_value"] == 0.0
    assert p["temp"]["max_value"] == 2.0
    assert p["temp"]["step"] == 0.05
    # pydantic Field(...) constraints live one level down in FieldInfo.metadata
    assert p["capped"]["min_value"] == 1.0
    assert p["capped"]["max_value"] == 4096.0


def test_annotated_dict_metadata_still_supported():
    def f(x: Annotated[float, {"min_value": 0.0, "max_value": 1.0, "step": 0.01}] = 0.5):
        return x

    p = TangleFunction(f).parameters
    assert p["x"]["min_value"] == 0.0 and p["x"]["max_value"] == 1.0 and p["x"]["step"] == 0.01


def test_optional_is_unwrapped():
    def f(x: Optional[int] = 3):
        return x

    assert TangleFunction(f).parameters["x"]["kind"] == "number"


def test_values_round_trip():
    tf = TangleFunction(_sample)
    tf.values = {**tf.values, "lr": 0.2}
    assert tf.values["lr"] == 0.2


def test_var_args_and_self_are_skipped():
    def f(self, a: int = 1, *args, **kwargs):
        return a

    assert TangleFunction(f).param_order == ["a"]


def test_invalid_inputs_raise():
    with pytest.raises(ValueError, match="callable"):
        TangleFunction(42)

    def needs_hint(x):  # no hint, no default
        return x

    with pytest.raises(ValueError, match="no type hint or default"):
        TangleFunction(needs_hint)

    def f(a: int = 1):
        return a

    with pytest.raises(ValueError, match="not found"):
        TangleFunction(f, params={"nope": {"value": 2}})

    def g(x: Annotated[int, {"min_value": 0, "max_value": 10}] = 5):
        return x

    with pytest.raises(ValueError, match="above max_value"):
        TangleFunction(g, params={"x": {"value": 99}})
