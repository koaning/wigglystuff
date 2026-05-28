"""Tests for CircularSlider and CircularRangeSlider widgets."""

import pytest

from wigglystuff import CircularRangeSlider, CircularSlider


def test_single_defaults_and_construction():
    s = CircularSlider()
    assert s.start == 0.0
    assert s.stop == 100.0
    assert s.step == 1.0
    assert s.value == 0.0
    assert s._mode == "single"


def test_single_custom_value():
    s = CircularSlider(start=0, stop=10, step=0.5, value=3.5)
    assert s.value == 3.5
    assert s.step == 0.5


def test_single_value_clamped_at_construction():
    s = CircularSlider(start=0, stop=10, value=42)
    assert s.value == 10
    s2 = CircularSlider(start=0, stop=10, value=-5)
    assert s2.value == 0


def test_single_invalid_bounds_raises():
    with pytest.raises(ValueError, match="start must be less than stop"):
        CircularSlider(start=10, stop=5)
    with pytest.raises(ValueError, match="start must be less than stop"):
        CircularSlider(start=5, stop=5)


def test_single_invalid_step_raises():
    with pytest.raises(ValueError, match="step must be positive"):
        CircularSlider(step=0)
    with pytest.raises(ValueError, match="step must be positive"):
        CircularSlider(step=-1)


def test_range_defaults_and_construction():
    r = CircularRangeSlider()
    assert r.start == 0.0
    assert r.stop == 100.0
    assert r.value == (0.0, 100.0)
    assert r._mode == "range"


def test_range_custom_value():
    r = CircularRangeSlider(start=0, stop=100, value=(20, 80))
    assert r.value == (20.0, 80.0)


def test_range_values_clamped_at_construction():
    r = CircularRangeSlider(start=0, stop=10, value=(-5, 42))
    assert r.value == (0.0, 10.0)


def test_range_unordered_value_is_sorted():
    # Construction accepts (low, high) in either order — sorting protects the
    # common case of users passing "min, max" out of order. Runtime drags may
    # still produce wrap-around (low > high) values, by design.
    r = CircularRangeSlider(value=(80, 20))
    assert r.value == (20.0, 80.0)


def test_range_runtime_can_wrap_seam():
    # The traitlet doesn't enforce low <= high after construction; this is
    # how the JS communicates "range crosses the 12 o'clock seam."
    r = CircularRangeSlider(start=0, stop=100, value=(20, 80))
    r.value = (80.0, 20.0)
    assert r.value == (80.0, 20.0)


def test_range_invalid_bounds_raises():
    with pytest.raises(ValueError, match="start must be less than stop"):
        CircularRangeSlider(start=10, stop=5)


def test_range_invalid_step_raises():
    with pytest.raises(ValueError, match="step must be positive"):
        CircularRangeSlider(step=0)


def test_size_too_small_raises():
    with pytest.raises(ValueError, match="too small to render"):
        CircularSlider(size=40)
    with pytest.raises(ValueError, match="too small to render"):
        CircularRangeSlider(size=50, thickness=18)


def test_size_minimum_just_passes():
    # Default thickness=18 → minimum = 2*18+30 = 66.
    s = CircularSlider(size=66)
    assert s.size == 66
    r = CircularRangeSlider(size=66)
    assert r.size == 66


def test_label_defaults_empty_and_sets_through():
    s = CircularSlider()
    assert s.label == ""
    s2 = CircularSlider(label="Temperature")
    assert s2.label == "Temperature"
    r = CircularRangeSlider(label="Window")
    assert r.label == "Window"


def test_color_defaults_empty_and_sets_through():
    s = CircularSlider()
    assert s.color == ""
    s2 = CircularSlider(color="#ef4444")
    assert s2.color == "#ef4444"
    r = CircularRangeSlider(color="tomato")
    assert r.color == "tomato"


def test_value_traitlet_sync():
    s = CircularSlider(start=0, stop=10, value=2)
    s.value = 7.5
    assert s.value == 7.5

    r = CircularRangeSlider(start=0, stop=10, value=(2, 8))
    r.value = (3, 6)
    assert r.value == (3.0, 6.0)
