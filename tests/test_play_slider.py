import pytest

from wigglystuff import PlaySlider


def test_defaults():
    s = PlaySlider()
    assert (s.min_value, s.max_value, s.step) == (0.0, 100.0, 1.0)
    assert s.value == 0.0
    assert s.playing is False
    assert s.loop is False


def test_construction_validates_bounds_and_step():
    with pytest.raises(ValueError):
        PlaySlider(min_value=5, max_value=5)
    with pytest.raises(ValueError):
        PlaySlider(step=0)


def test_values_reaches_max_with_float_drift_step():
    # max_value is an exact multiple of step, but adding 0.05 twenty times
    # gives 1.0000000000000002; the endpoint must still be included.
    s = PlaySlider(min_value=0, max_value=1, step=0.05)
    values = s.values
    assert len(values) == 21
    assert values[-1] == 1.0
    assert values[0] == 0.0


def test_values_reaches_max_integer_step():
    s = PlaySlider(min_value=0, max_value=10, step=1)
    assert s.values == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_values_non_exact_multiple_stops_below_max():
    # 2 / 0.7 is not an integer, so the range should stop at the last value
    # <= max_value rather than overshoot it.
    s = PlaySlider(min_value=0, max_value=2, step=0.7)
    assert s.values == [0.0, 0.7, 1.4]


def test_values_precision_follows_step_and_min_value():
    # Scientific-notation steps used to read as 0 decimals, collapsing every
    # value to 0 or 1.
    tiny = PlaySlider(min_value=0, max_value=0.0001, step=1e-05).values
    assert len(tiny) == 11
    assert tiny[1] == 1e-05 and tiny[-1] == 0.0001
    # min_value's decimals count too, so 0.25 is not rounded down to 0.2.
    offset = PlaySlider(min_value=0.25, max_value=0.65, step=0.1).values
    assert offset == [0.25, 0.35, 0.45, 0.55, 0.65]
