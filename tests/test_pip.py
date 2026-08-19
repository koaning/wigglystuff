import pytest
import traitlets

from wigglystuff import Knob, Pip


def test_constructor():
    knob = Knob(label="gain")
    p = Pip(knob, width=320, height=280)
    assert p.child is knob
    assert (p.width, p.height) == (320, 280)
    # Starts docked; only a user gesture can open the window.
    assert p.floating is False

    default = Pip(knob)
    assert (default.width, default.height) == (400, 300)


def test_child_serializes_as_a_widget_ref():
    knob = Knob(label="gain")
    assert Pip(knob).get_state()["child"] == f"anywidget:{knob.model_id}"


def test_child_must_be_a_widget():
    for bad in ["<div>hi</div>", 42, object()]:
        with pytest.raises(traitlets.TraitError):
            Pip(bad)


def test_size_must_be_positive():
    knob = Knob()
    for kwargs in ({"width": 0}, {"width": -1}, {"height": 0}, {"height": -20}):
        with pytest.raises(ValueError):
            Pip(knob, **kwargs)

    # and the check still applies after construction
    p = Pip(knob)
    with pytest.raises(ValueError):
        p.width = 0


def test_floating_is_writable_from_python():
    # Setting False is how Python closes the window; the JS side ignores True.
    p = Pip(Knob())
    p.floating = True
    assert p.floating is True
    p.floating = False
    assert p.floating is False
