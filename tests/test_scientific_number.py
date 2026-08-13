"""Tests for the ScientificNumber widget. (AI generated)"""

import pytest
import traitlets

from wigglystuff.scientific_number import ScientificNumber


def test_defaults():
    s = ScientificNumber()
    assert s.value == 0
    assert s.raw_value == 0
    assert s.scale == 1.0
    assert s.scale_label == ""
    assert s.label == ""
    assert s.unit_label == ""
    assert s.step is None
    assert s.min is None
    assert s.max is None


def test_value_applies_scale():
    s = ScientificNumber(value=2e3, scale=1e3, scale_label="k")
    assert s.raw_value == 2
    assert s.value == 2000


def test_scientific_notation_value():
    s = ScientificNumber(value=2.34e-8)
    assert s.value == 2.34e-8


def test_step_snaps_raw_input():
    s = ScientificNumber(step=0.5, value=2.73)
    assert s.raw_value == 2.5
    assert s.value == 2.5


def test_step_precision_kills_float_noise():
    s = ScientificNumber(scale=1e3, step=1e-3, value=2.002e3)
    assert s.raw_value == 2.002
    assert s.value == 2002.0
    s.raw_value = 0.1 + 0.2
    assert s.raw_value == 0.3
    assert s.value == 300.0


def test_min_max_clamp_scaled_value():
    low = ScientificNumber(min=0, max=100, value=-5)
    assert low.value == 0
    assert low.raw_value == 0
    high = ScientificNumber(min=0, max=100, value=150)
    assert high.value == 100
    assert high.raw_value == 100


def test_scale_respects_limits():
    s = ScientificNumber(scale=1e3, min=0, max=5e6, value=1e7)
    assert s.raw_value == 5000
    assert s.value == 5e6


def test_setting_value_from_python_snaps_and_scales():
    s = ScientificNumber(scale=1e3, step=1, value=2e3)
    s.value = 3450
    assert s.value == 3000
    assert s.raw_value == 3


def test_constructor_guards():
    with pytest.raises(traitlets.TraitError, match="scale must be positive"):
        ScientificNumber(scale=0)
    with pytest.raises(traitlets.TraitError, match="scale must be positive"):
        ScientificNumber(scale=0, value=5)
    with pytest.raises(traitlets.TraitError, match="step must be positive"):
        ScientificNumber(step=0)
    with pytest.raises(traitlets.TraitError, match="min must be less than max"):
        ScientificNumber(min=10, max=5)


def test_post_init_guards():
    s = ScientificNumber()
    with pytest.raises(traitlets.TraitError, match="positive"):
        s.scale = 0
    with pytest.raises(traitlets.TraitError, match="positive"):
        s.step = -1

    s = ScientificNumber(max=5)
    with pytest.raises(traitlets.TraitError, match="min must be less than max"):
        s.min = 10

    s = ScientificNumber(min=10)
    with pytest.raises(traitlets.TraitError, match="min must be less than max"):
        s.max = 5


def test_width():
    assert ScientificNumber(width=200).width == 200


def test_getter_scheme():
    s = ScientificNumber(scale=1e3, unit_label="$\\text{m}$", value=2e3)
    assert s.value == 2000
    assert s.raw_value == 2
    assert s.scale == 1000.0
    assert s.unit_label == "$\\text{m}$"


def test_scaled_value_alias():
    s = ScientificNumber(scale=1e3, step=1, value=2e3)
    assert s.scaled_value == 2000
    s.value = 3450
    assert s.scaled_value == 3000
    s.raw_value = 5.5
    assert s.raw_value == 6
    assert s.scaled_value == 6000
    s.scaled_value = 4000
    assert s.value == 4000
    assert s.raw_value == 4


def test_wrapped_value_dict_contains_scaled_value():
    import marimo as mo

    w = mo.ui.anywidget(ScientificNumber(scale=1e3, value=2e3))
    assert w.value["value"] == 2000
    assert w.value["scaled_value"] == 2000
    assert w.value["raw_value"] == 2
    assert w.scaled_value == 2000
    assert w.raw_value == 2


def test_inline_mode():
    s = ScientificNumber()
    assert s.inline_mode is False
    s.inline()
    assert s.inline_mode is True
    assert ScientificNumber(inline_mode=True).inline_mode is True


# --- notation -----------------------------------------------------------------


def test_notation_defaults_to_decimal():
    s = ScientificNumber()
    assert s.notation == "decimal"


def test_notation_accepts_scientific():
    s = ScientificNumber(notation="scientific")
    assert s.notation == "scientific"


def test_notation_rejects_invalid():
    with pytest.raises(traitlets.TraitError, match="notation"):
        ScientificNumber(notation="binary")
