"""Tests for the TangleSlider widget."""

from wigglystuff import TangleSlider


def test_committed_amount_holds_old_value_during_drag():
    slider = TangleSlider(amount=5, min_value=0, max_value=10)
    assert slider.committed_amount == 5
    assert slider.dragging is False

    # Outside a drag, a Python-side change moves the committed value too.
    slider.amount = 7
    assert slider.committed_amount == 7

    # Mid-drag, amount follows along while committed_amount keeps the old value.
    slider.dragging = True
    slider.amount = 9
    assert slider.committed_amount == 7
