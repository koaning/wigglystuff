import pytest

from wigglystuff import MidiButton


def test_defaults_and_midi_key_falls_back_to_label():
    btn = MidiButton(label="Fire")
    assert btn.mode == "momentary"
    assert btn.value is False
    assert btn.midi is True  # MIDI on by default for a MidiButton
    assert btn.midi_note == -1
    # midi_key is empty; the JS falls back to the label for persistence.
    assert btn.midi_key == ""
    assert btn.label == "Fire"


def test_mode_validation():
    with pytest.raises(ValueError):
        MidiButton(mode="bogus")


def test_value_coercion_and_toggle_initial_state():
    assert MidiButton(mode="toggle", value=True).value is True
    assert MidiButton(mode="toggle", value=1).value is True
    assert MidiButton(mode="momentary").value is False
