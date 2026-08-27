"""Tests for the FormulaAnimation widget's Python API."""

import pytest

from wigglystuff.formula_animation import FormulaAnimation


def test_defaults_and_note_normalization_without_mutating_input():
    steps = [{"tex": "x = 1"}, {"tex": "y = 2", "note": "second"}]
    widget = FormulaAnimation(steps=steps)

    # A missing note becomes "" and the caller's input is left untouched.
    assert widget.steps == [
        {"tex": "x = 1", "note": ""},
        {"tex": "y = 2", "note": "second"},
    ]
    assert steps == [{"tex": "x = 1"}, {"tex": "y = 2", "note": "second"}]

    # Defaults.
    assert widget.step == 0
    assert widget.spotlight is True
    assert widget.height == 360
    assert widget.theme == "auto"
    assert widget.title is None


def test_non_default_arguments_are_stored():
    widget = FormulaAnimation(
        steps=[{"tex": "a"}],
        title="Heading",
        spotlight=False,
        height=200,
        theme="dark",
    )
    assert widget.title == "Heading"
    assert widget.spotlight is False
    assert widget.height == 200
    assert widget.theme == "dark"


def test_step_updates_fire_observers():
    widget = FormulaAnimation(steps=[{"tex": "a"}, {"tex": "b"}])
    seen = []
    widget.observe(lambda change: seen.append(change["new"]), names="step")
    widget.step = 1
    assert seen == [1]


@pytest.mark.parametrize(
    "steps, message",
    [
        ([], "at least one step"),
        ("x = 1", "list of dicts"),
        ({"tex": "x"}, "list of dicts"),
        ([{"note": "no tex"}], "non-empty string 'tex'"),
        ([{"tex": ""}], "non-empty string 'tex'"),
        ([{"tex": "   "}], "non-empty string 'tex'"),
        ([{"tex": 3}], "non-empty string 'tex'"),
        (["x = 1"], "must be a mapping"),
        ([{"tex": "x", "note": 5}], "'note' must be a string"),
    ],
)
def test_invalid_steps_raise(steps, message):
    with pytest.raises(ValueError, match=message):
        FormulaAnimation(steps=steps)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"theme": "blue"}, "theme must be"),
        ({"height": 0}, "height must be a positive integer"),
        ({"height": -5}, "height must be a positive integer"),
        ({"height": True}, "height must be a positive integer"),
        ({"title": 5}, "title must be a string"),
    ],
)
def test_invalid_options_raise(kwargs, message):
    with pytest.raises(ValueError, match=message):
        FormulaAnimation(steps=[{"tex": "x"}], **kwargs)
