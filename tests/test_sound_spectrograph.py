from io import BytesIO
import wave

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("librosa")

from wigglystuff.sound_spectrograph import SoundSpectrograph


def sine_wave(sample_rate=22050, seconds=1.0, frequency=440.0):
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    return 0.4 * np.sin(2 * np.pi * frequency * t)


def wav_bytes(audio, sample_rate):
    samples = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())
    return buffer.getvalue()


def make_widget(audio=None, sample_rate=22050, **kwargs):
    if audio is None:
        audio = sine_wave(sample_rate=sample_rate)
    options = {
        "n_fft": 512,
        "hop_length": 128,
        "width": 240,
        "height": 160,
    }
    options.update(kwargs)
    return SoundSpectrograph(
        audio,
        sample_rate=sample_rate,
        **options,
    )


def test_sound_spectrograph_from_array_renders_spectrogram():
    widget = make_widget()

    assert widget.sample_rate == 22050
    assert widget.duration == pytest.approx(1.0)
    assert widget.time_bounds == pytest.approx((0.0, 1.0))
    assert widget.frequency_bounds == pytest.approx((0.0, 11025.0))
    assert widget.selection_groups == [
        {"id": "region-1", "name": "Region 1", "color": "#06b6d4", "enabled": True}
    ]
    assert widget.active_group_index == 0
    assert widget.mode == "box"
    assert widget.modes == ["box", "lasso"]
    assert widget.spectrogram_base64.startswith("data:image/png;base64,")


def test_sound_spectrograph_accepts_tuple_input():
    sample_rate = 16000
    widget = SoundSpectrograph(
        (sine_wave(sample_rate=sample_rate), sample_rate),
        n_fft=512,
        hop_length=128,
    )

    assert widget.sample_rate == sample_rate
    assert widget.duration == pytest.approx(1.0)


def test_sound_spectrograph_accepts_bytes_and_paths(tmp_path):
    sample_rate = 22050
    audio = sine_wave(sample_rate=sample_rate)
    payload = wav_bytes(audio, sample_rate)

    bytes_widget = make_widget(payload, sample_rate=sample_rate)
    assert bytes_widget.duration == pytest.approx(1.0)

    path = tmp_path / "tone.wav"
    path.write_bytes(payload)
    path_widget = make_widget(path, sample_rate=sample_rate)
    assert path_widget.duration == pytest.approx(1.0)


def test_empty_selection_mask_is_false():
    widget = make_widget()

    mask = widget.get_selection_mask()

    assert mask.shape == widget._stft.shape
    assert not mask.any()


def test_lasso_selection_mask_selects_bins():
    widget = make_widget()
    widget.selections = [
        {
            "type": "lasso",
            "vertices": [
                [0.0, 300.0],
                [widget.duration, 300.0],
                [widget.duration, 700.0],
                [0.0, 700.0],
            ],
        }
    ]

    mask = widget.get_selection_mask()

    assert mask.any()


def test_multiple_selections_are_combined():
    widget = make_widget()
    low_region = {
        "type": "lasso",
        "vertices": [[0.0, 300.0], [1.0, 300.0], [1.0, 700.0], [0.0, 700.0]],
    }
    high_region = {
        "type": "lasso",
        "vertices": [[0.0, 900.0], [1.0, 900.0], [1.0, 1300.0], [0.0, 1300.0]],
    }

    widget.selections = [low_region]
    single_count = int(widget.get_selection_mask().sum())
    widget.selections = [low_region, high_region]
    combined_count = int(widget.get_selection_mask().sum())

    assert combined_count > single_count


def test_selection_mode_can_start_with_lasso_only():
    widget = make_widget(mode="lasso", modes=["lasso"])

    assert widget.mode == "lasso"
    assert widget.modes == ["lasso"]


def test_disabled_selection_groups_do_not_contribute_to_mask():
    widget = make_widget()
    second_group = widget.add_selection_group()
    first_group = widget.selection_groups[0]
    widget.selections = [
        {
            "type": "box",
            "group_id": first_group["id"],
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": 300.0,
            "y_max": 700.0,
        },
        {
            "type": "box",
            "group_id": second_group["id"],
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": 900.0,
            "y_max": 1300.0,
        },
    ]

    combined_count = int(widget.get_selection_mask().sum())
    widget.set_group_enabled(1, False)
    enabled_count = int(widget.get_selection_mask().sum())
    widget.set_group_enabled(0, False)
    disabled_count = int(widget.get_selection_mask().sum())

    assert combined_count > enabled_count > disabled_count
    assert disabled_count == 0


def test_selection_without_group_id_uses_first_group():
    widget = make_widget()
    widget.selections = [
        {"type": "box", "x_min": 0.0, "x_max": 1.0, "y_min": 300.0, "y_max": 700.0}
    ]

    assert widget.get_selection_mask().any()

    widget.set_group_enabled(0, False)
    assert not widget.get_selection_mask().any()


def test_get_selected_audio_without_selection_returns_full_audio():
    widget = make_widget()

    selected = widget.get_selected_audio()

    assert selected.shape == widget._audio.shape
    assert np.allclose(selected, widget._audio)


def test_play_request_without_selection_encodes_full_audio():
    widget = make_widget()

    widget.play_request_id = 1

    assert widget.playback_error == ""
    assert widget.selected_audio_base64.startswith("data:audio/wav;base64,")
    assert widget.selected_audio_duration == pytest.approx(widget.duration)


def test_play_request_with_only_disabled_selection_sets_error():
    widget = make_widget()
    widget.selections = [
        {"type": "box", "x_min": 0.0, "x_max": 1.0, "y_min": 300.0, "y_max": 700.0}
    ]
    widget.set_group_enabled(0, False)

    widget.play_request_id = 1

    assert widget.playback_error == "Enable at least one selection region before playback."
    assert widget.selected_audio_base64 == ""


def test_play_request_with_empty_enabled_selection_sets_error():
    widget = make_widget()
    widget.selections = [
        {"type": "box", "x_min": 0.0, "x_max": 0.01, "y_min": 50_000.0, "y_max": 60_000.0}
    ]

    widget.play_request_id = 1

    assert widget.playback_error == (
        "Selection does not cover any audio bins. Try a larger or different region."
    )
    assert widget.selected_audio_base64 == ""


def test_log_spectrogram_uses_log_frequency_rows():
    widget = make_widget(frequency_scale="log", height=120)

    from wigglystuff.sound_spectrograph import _spectrogram_row_indices

    log_rows = _spectrogram_row_indices(
        widget._display_values.shape[0],
        widget.height,
        frequency_scale="log",
        frequencies=widget._frequencies,
    )
    linear_rows = _spectrogram_row_indices(
        widget._display_values.shape[0],
        widget.height,
        frequency_scale="linear",
        frequencies=widget._frequencies,
    )

    assert not np.array_equal(log_rows, linear_rows)
    assert log_rows[0] > log_rows[-1]


def test_play_request_with_selection_encodes_wav():
    widget = make_widget()
    widget.selections = [
        {"type": "box", "x_min": 0.0, "x_max": 1.0, "y_min": 300.0, "y_max": 700.0}
    ]

    widget.play_request_id = 1

    selected = widget.get_selected_audio()

    assert selected.shape == widget._audio.shape
    assert widget.selected_audio_base64.startswith("data:audio/wav;base64,")
    assert widget.selected_audio_duration == pytest.approx(1.0)
    assert widget.playback_error == ""


def test_selected_audio_trims_to_selected_time_span():
    widget = make_widget()
    widget.selections = [
        {"type": "box", "x_min": 0.25, "x_max": 0.45, "y_min": 300.0, "y_max": 700.0}
    ]

    trimmed = widget.get_selected_audio()
    full_length = widget.get_selected_audio(trim=False)

    assert len(trimmed) < len(full_length)
    assert len(full_length) == len(widget._audio)


def test_clear_resets_selection_state():
    widget = make_widget()
    widget.selections = [{"type": "box", "x_min": 0.0, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0}]
    widget.selected_index = 0
    widget.playback_error = "problem"

    widget.clear()

    assert widget.selections == []
    assert widget.selected_index == -1
    assert widget.playback_error == ""


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"width": 0}, "width must be positive"),
        ({"height": 0}, "height must be positive"),
        ({"n_fft": 1}, "n_fft must be at least 2"),
        ({"hop_length": 0}, "hop_length must be at least 1"),
        ({"frequency_scale": "mel"}, 'frequency_scale must be "linear" or "log"'),
        ({"colormap": "plasma"}, "colormap must be one of"),
        ({"mode": "circle"}, 'mode must be "box" or "lasso"'),
        ({"modes": []}, "modes must include at least one selection mode"),
        ({"modes": ["box", "circle"]}, 'modes may only include "box" and "lasso"'),
    ],
)
def test_validation(kwargs, error):
    with pytest.raises(Exception, match=error):
        make_widget(**kwargs)


def test_array_input_requires_sample_rate():
    with pytest.raises(ValueError, match="sample_rate is required"):
        SoundSpectrograph(sine_wave(), n_fft=512, hop_length=128)