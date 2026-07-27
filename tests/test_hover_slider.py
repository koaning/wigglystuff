"""Tests for the HoverSlider widget."""

import pytest
import traitlets

from wigglystuff import HoverSlider


def test_defaults():
    s = HoverSlider()
    assert (s.start, s.stop, s.step) == (0, 100, 1)
    assert s.value == 0
    assert s.hover_value == 0
    assert s.hovering is False
    assert s.steps == []


def test_linear_dtype_is_preserved():
    ints = HoverSlider(start=0, stop=10, step=1, value=3)
    assert ints.value == 3 and isinstance(ints.value, int)
    # A single float anywhere makes the whole slider float, like mo.ui.slider.
    floats = HoverSlider(start=0, stop=10, step=1, value=2.5)
    assert isinstance(floats.value, float)
    assert isinstance(HoverSlider(start=0.0, stop=1.0, step=0.05).value, float)


def test_steps_mode_dtype_and_bounds():
    ints = HoverSlider(steps=[1, 10, 100, 1000])
    assert ints.value == 1 and isinstance(ints.value, int)
    assert (ints.start, ints.stop) == (1, 1000)
    assert ints.step is None  # meaningless in steps mode, mirroring mo.ui.slider
    floats = HoverSlider(steps=[1, 2.5, 4])
    assert floats.steps == [1.0, 2.5, 4.0]
    assert isinstance(floats.value, float)


def test_values_snap_into_range():
    s = HoverSlider(steps=[1, 10, 100], value=7)
    assert s.value == 10  # nearest entry, not truncated
    linear = HoverSlider(start=0, stop=10, step=1)
    linear.value = 4.7
    assert linear.value == 5
    linear.value = 999
    assert linear.value == 10


def test_hover_value_mirrors_value_only_when_not_hovering():
    s = HoverSlider(start=0, stop=10, step=1, value=2)
    s.value = 8
    assert s.hover_value == 8
    # While the pointer is on the track the ghost stays put as `value` moves.
    s.hovering = True
    s.value = 3
    assert s.hover_value == 8


def test_numpy_steps_are_normalised():
    np = pytest.importorskip("numpy")
    s = HoverSlider(steps=np.array([1, 2, 3]))
    assert s.steps == [1, 2, 3]
    assert isinstance(s.value, int)


def test_constructor_guards():
    with pytest.raises(ValueError, match="mutually exclusive"):
        HoverSlider(steps=[1, 2], start=0)
    with pytest.raises(ValueError, match="at least two steps"):
        HoverSlider(steps=[1])
    with pytest.raises(TypeError, match="sequence of numbers"):
        HoverSlider(steps=[1, "a"])
    with pytest.raises(TypeError, match="sequence of numbers"):
        HoverSlider(steps=[True, 2])  # bool is an int subclass; reject it anyway
    with pytest.raises(ValueError, match="start must be less than stop"):
        HoverSlider(start=10, stop=5)
    with pytest.raises(ValueError, match="step must be positive"):
        HoverSlider(step=0)


def test_sync_throttle_ms_must_be_non_negative():
    assert HoverSlider(sync_throttle_ms=0).sync_throttle_ms == 0
    with pytest.raises(traitlets.TraitError, match="non-negative"):
        HoverSlider(sync_throttle_ms=-1)
