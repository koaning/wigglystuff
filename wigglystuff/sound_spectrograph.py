"""Interactive sound spectrogram widget with lasso-based playback masks."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
import struct
from typing import Any
import wave
import zlib

import anywidget
import traitlets


PALETTES = {
    "gray": [(0.0, (0, 0, 0)), (1.0, (255, 255, 255))],
    "magma": [
        (0.0, (0, 0, 4)),
        (0.25, (80, 18, 123)),
        (0.5, (182, 54, 121)),
        (0.75, (251, 136, 97)),
        (1.0, (252, 253, 191)),
    ],
    "viridis": [
        (0.0, (68, 1, 84)),
        (0.25, (59, 82, 139)),
        (0.5, (33, 145, 140)),
        (0.75, (94, 201, 98)),
        (1.0, (253, 231, 37)),
    ],
}

REGION_COLORS = ["#06b6d4", "#f97316", "#84cc16", "#ec4899", "#8b5cf6"]


class SoundSpectrograph(anywidget.AnyWidget):
    """Visualize audio as a spectrogram and play back selected bins.

    ``SoundSpectrograph`` computes an STFT with ``librosa`` and shows the
    spectrogram in the browser. Draw one or more box or lasso selections over
    the spectrogram; playback reconstructs a single audio clip from the
    combined selected time-frequency bins.

    Examples:
        ```python
        import numpy as np
        from wigglystuff import SoundSpectrograph

        sr = 22_050
        t = np.arange(sr) / sr
        audio = np.sin(2 * np.pi * 440 * t)

        widget = SoundSpectrograph(audio, sample_rate=sr)
        widget
        ```
    """

    _esm = Path(__file__).parent / "static" / "sound-spectrograph.js"
    _css = Path(__file__).parent / "static" / "sound-spectrograph.css"

    spectrogram_base64 = traitlets.Unicode("").tag(sync=True)
    width = traitlets.Int(700).tag(sync=True)
    height = traitlets.Int(420).tag(sync=True)
    duration = traitlets.Float(0.0).tag(sync=True)
    sample_rate = traitlets.Int(0).tag(sync=True)
    time_bounds = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)
    frequency_bounds = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)
    frequency_scale = traitlets.Unicode("linear").tag(sync=True)
    colormap = traitlets.Unicode("magma").tag(sync=True)
    mode = traitlets.Unicode("box").tag(sync=True)
    modes = traitlets.List(
        traitlets.Unicode(), default_value=["box", "lasso"]
    ).tag(sync=True)

    selection_groups = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    active_group_index = traitlets.Int(0).tag(sync=True)
    selections = traitlets.List(traitlets.Dict(), default_value=[]).tag(sync=True)
    selected_index = traitlets.Int(-1).tag(sync=True)
    selection_opacity = traitlets.Float(0.28).tag(sync=True)
    stroke_width = traitlets.Int(2).tag(sync=True)

    play_request_id = traitlets.Int(0).tag(sync=True)
    selected_audio_base64 = traitlets.Unicode("").tag(sync=True)
    selected_audio_duration = traitlets.Float(0.0).tag(sync=True)
    is_playing = traitlets.Bool(False).tag(sync=True)
    playback_error = traitlets.Unicode("").tag(sync=True)

    n_fft = traitlets.Int(2048).tag(sync=True)
    hop_length = traitlets.Int(512).tag(sync=True)
    window = traitlets.Unicode("hann").tag(sync=True)
    power = traitlets.Float(2.0).tag(sync=True)

    def __init__(
        self,
        audio: Any,
        *,
        sample_rate: int | None = None,
        mono: bool = True,
        n_fft: int = 2048,
        hop_length: int | None = None,
        window: str = "hann",
        power: float = 2.0,
        db_ref: float = 1.0,
        db_range: float = 80.0,
        frequency_scale: str = "linear",
        colormap: str = "magma",
        mode: str = "box",
        modes: list[str] | None = None,
        width: int = 700,
        height: int = 420,
        selection_opacity: float = 0.28,
        stroke_width: int = 2,
        **kwargs: Any,
    ) -> None:
        """Create a sound spectrogram widget.

        Args:
            audio: Path, bytes, file-like object, array-like waveform, or
                ``(waveform, sample_rate)`` tuple.
            sample_rate: Target sample rate for file inputs, or the source
                sample rate for raw arrays. Required for raw arrays unless
                ``audio`` is a ``(waveform, sample_rate)`` tuple.
            mono: Convert multi-channel inputs to mono.
            n_fft: STFT window size.
            hop_length: Number of samples between STFT frames. Defaults to
                ``n_fft // 4``.
            window: Librosa window name.
            power: Exponent used before converting magnitudes to decibels.
            db_ref: Reference value for ``librosa.power_to_db``.
            db_range: Dynamic range, in dB, used for the rendered image.
            frequency_scale: ``"linear"`` or ``"log"`` display scale.
            colormap: ``"magma"``, ``"viridis"``, or ``"gray"``.
            mode: Initial selection mode, ``"box"`` or ``"lasso"``.
            modes: Available selection modes. Defaults to ``["box", "lasso"]``.
            width: Widget width in pixels.
            height: Spectrogram canvas height in pixels.
            selection_opacity: Fill opacity for lasso regions.
            stroke_width: Selection outline width in pixels.
            **kwargs: Forwarded to ``AnyWidget``.
        """
        if hop_length is None:
            hop_length = max(1, n_fft // 4)
        if modes is None:
            modes = ["box", "lasso"]

        self._db_ref = db_ref
        self._db_range = db_range
        self._audio, loaded_sample_rate = _load_audio(audio, sample_rate, mono=mono)
        self._stft = None
        self._magnitudes = None
        self._display_values = None
        self._frequencies = None
        self._times = None
        selection_groups = kwargs.pop("selection_groups", _default_selection_groups())
        active_group_index = kwargs.pop("active_group_index", 0)

        super().__init__(
            width=width,
            height=height,
            sample_rate=loaded_sample_rate,
            duration=len(self._audio) / loaded_sample_rate,
            time_bounds=(0.0, len(self._audio) / loaded_sample_rate),
            frequency_bounds=(0.0, loaded_sample_rate / 2),
            frequency_scale=frequency_scale,
            colormap=colormap,
            mode=mode,
            modes=modes,
            n_fft=n_fft,
            hop_length=hop_length,
            window=window,
            power=power,
            selection_groups=selection_groups,
            active_group_index=active_group_index,
            selection_opacity=selection_opacity,
            stroke_width=stroke_width,
            **kwargs,
        )
        self._compute_spectrogram()
        self.spectrogram_base64 = _spectrogram_png_base64(
            self._display_values,
            width=self.width,
            height=self.height,
            colormap=self.colormap,
            db_range=self._db_range,
            frequency_scale=self.frequency_scale,
            frequencies=self._frequencies,
        )

    @traitlets.validate("width", "height")
    def _validate_positive_size(self, proposal: dict[str, Any]) -> int:
        value = proposal["value"]
        if value <= 0:
            raise traitlets.TraitError(f"{proposal['trait'].name} must be positive.")
        return value

    @traitlets.validate("n_fft")
    def _validate_n_fft(self, proposal: dict[str, Any]) -> int:
        value = proposal["value"]
        if value < 2:
            raise traitlets.TraitError("n_fft must be at least 2.")
        return value

    @traitlets.validate("hop_length")
    def _validate_hop_length(self, proposal: dict[str, Any]) -> int:
        value = proposal["value"]
        if value < 1:
            raise traitlets.TraitError("hop_length must be at least 1.")
        return value

    @traitlets.validate("power")
    def _validate_power(self, proposal: dict[str, Any]) -> float:
        value = proposal["value"]
        if value <= 0:
            raise traitlets.TraitError("power must be positive.")
        return value

    @traitlets.validate("frequency_scale")
    def _validate_frequency_scale(self, proposal: dict[str, Any]) -> str:
        value = proposal["value"]
        if value not in {"linear", "log"}:
            raise traitlets.TraitError('frequency_scale must be "linear" or "log".')
        return value

    @traitlets.validate("colormap")
    def _validate_colormap(self, proposal: dict[str, Any]) -> str:
        value = proposal["value"]
        if value not in PALETTES:
            valid = '", "'.join(PALETTES)
            raise traitlets.TraitError(f'colormap must be one of "{valid}".')
        return value

    @traitlets.validate("mode")
    def _validate_mode(self, proposal: dict[str, Any]) -> str:
        value = proposal["value"]
        if value not in {"box", "lasso"}:
            raise traitlets.TraitError('mode must be "box" or "lasso".')
        return value

    @traitlets.validate("modes")
    def _validate_modes(self, proposal: dict[str, Any]) -> list[str]:
        values = proposal["value"]
        if not values:
            raise traitlets.TraitError("modes must include at least one selection mode.")
        invalid = [value for value in values if value not in {"box", "lasso"}]
        if invalid:
            raise traitlets.TraitError('modes may only include "box" and "lasso".')
        return values

    @traitlets.validate("selection_opacity")
    def _validate_selection_opacity(self, proposal: dict[str, Any]) -> float:
        value = proposal["value"]
        if not 0 <= value <= 1:
            raise traitlets.TraitError("selection_opacity must be between 0 and 1.")
        return value

    @traitlets.validate("stroke_width")
    def _validate_stroke_width(self, proposal: dict[str, Any]) -> int:
        value = proposal["value"]
        if value < 1:
            raise traitlets.TraitError("stroke_width must be at least 1.")
        return value

    @traitlets.observe("play_request_id")
    def _on_play_request(self, change: dict[str, Any]) -> None:
        if change["new"] == change["old"]:
            return
        try:
            selected_audio = self.get_selected_audio()
        except ValueError as exc:
            self.playback_error = str(exc)
            return

        self.playback_error = ""
        self.selected_audio_duration = len(selected_audio) / self.sample_rate
        self.selected_audio_base64 = _audio_wav_base64(selected_audio, self.sample_rate)

    def clear(self) -> None:
        """Remove all selections and clear playback errors."""
        self.selections = []
        self.selected_index = -1
        self.playback_error = ""

    def add_selection_group(
        self,
        name: str | None = None,
        color: str | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a new selection group and make it active."""
        groups = list(self.selection_groups)
        group_number = len(groups) + 1
        group = {
            "id": f"region-{group_number}",
            "name": name or f"Region {group_number}",
            "color": color or REGION_COLORS[(group_number - 1) % len(REGION_COLORS)],
            "enabled": bool(enabled),
        }
        groups.append(group)
        self.selection_groups = groups
        self.active_group_index = len(groups) - 1
        return group

    def set_group_enabled(self, index: int, enabled: bool) -> None:
        """Toggle whether a selection group contributes to display/playback."""
        groups = [dict(group) for group in self.selection_groups]
        if not 0 <= index < len(groups):
            raise IndexError("selection group index out of range")
        groups[index]["enabled"] = bool(enabled)
        self.selection_groups = groups

    def get_selection_mask(self):
        """Return a boolean STFT-bin mask for enabled selection groups."""
        import numpy as np

        self._ensure_spectrogram()
        mask = np.zeros(self._stft.shape, dtype=bool)
        if not self.selections:
            return mask

        enabled_group_ids = self._enabled_group_ids()
        if self.selection_groups and not enabled_group_ids:
            return mask

        times = self._times
        frequencies = self._frequencies
        time_grid, frequency_grid = np.meshgrid(times, frequencies)
        if self.frequency_scale == "log":
            frequency_grid = _safe_log10(frequency_grid)

        for selection in self.selections:
            if not self._selection_is_enabled(selection, enabled_group_ids):
                continue
            mask |= self._selection_mask(selection, time_grid, frequency_grid)
        return mask

    def get_selected_audio(self, trim: bool = True):
        """Reconstruct and return audio from the combined selected bins.

        Args:
            trim: If ``True``, remove leading/trailing silence outside the
                selected time span. Pass ``False`` to keep the original audio
                length with unselected bins silenced.
        """
        import librosa
        import numpy as np

        mask = self.get_selection_mask()
        if not mask.any():
            if self.selections:
                if not self._has_enabled_selections():
                    raise ValueError("Enable at least one selection region before playback.")
                raise ValueError(
                    "Selection does not cover any audio bins. Try a larger or different region."
                )
            return np.asarray(self._audio, dtype=float)

        selected_stft = np.where(mask, self._stft, 0)
        audio = librosa.istft(
            selected_stft,
            hop_length=self.hop_length,
            window=self.window,
            length=len(self._audio),
        )
        if trim:
            columns = np.where(mask.any(axis=0))[0]
            start_sample = max(0, int(columns[0] * self.hop_length))
            end_sample = min(
                len(audio), int((columns[-1] + 1) * self.hop_length + self.n_fft)
            )
            audio = audio[start_sample:end_sample]
        return np.asarray(audio, dtype=float)

    def save_selected_audio(self, path: str | Path) -> Path:
        """Save the current selected reconstruction as a WAV file."""
        audio = self.get_selected_audio()
        path = Path(path)
        path.write_bytes(_audio_wav_bytes(audio, self.sample_rate))
        return path

    def set_audio(
        self,
        audio: Any,
        *,
        sample_rate: int | None = None,
        mono: bool = True,
    ) -> None:
        """Replace the audio source and recompute the spectrogram."""
        self._audio, loaded_sample_rate = _load_audio(audio, sample_rate, mono=mono)
        self.sample_rate = loaded_sample_rate
        self.duration = len(self._audio) / loaded_sample_rate
        self.time_bounds = (0.0, self.duration)
        self.frequency_bounds = (0.0, loaded_sample_rate / 2)
        self.clear()
        self._compute_spectrogram()
        self.spectrogram_base64 = _spectrogram_png_base64(
            self._display_values,
            width=self.width,
            height=self.height,
            colormap=self.colormap,
            db_range=self._db_range,
            frequency_scale=self.frequency_scale,
            frequencies=self._frequencies,
        )

    def _ensure_spectrogram(self) -> None:
        if self._stft is None:
            self._compute_spectrogram()

    def _compute_spectrogram(self) -> None:
        import librosa
        import numpy as np

        self._stft = librosa.stft(
            self._audio,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
            window=self.window,
        )
        self._magnitudes = np.abs(self._stft)
        powered = self._magnitudes**self.power
        self._display_values = librosa.power_to_db(powered, ref=self._db_ref)
        self._frequencies = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.n_fft)
        self._times = librosa.frames_to_time(
            np.arange(self._stft.shape[1]),
            sr=self.sample_rate,
            hop_length=self.hop_length,
        )

    def _selection_mask(self, selection: dict[str, Any], time_grid, frequency_grid):
        import numpy as np

        selection_type = selection.get("type", "lasso")
        if selection_type == "box":
            x_min = selection.get("x_min")
            x_max = selection.get("x_max")
            y_min = selection.get("y_min")
            y_max = selection.get("y_max")
            if None in {x_min, x_max, y_min, y_max}:
                return np.zeros(self._stft.shape, dtype=bool)
            if self.frequency_scale == "log":
                y_min = _safe_log10_value(y_min)
                y_max = _safe_log10_value(y_max)
            return (
                (time_grid >= min(x_min, x_max))
                & (time_grid <= max(x_min, x_max))
                & (frequency_grid >= min(y_min, y_max))
                & (frequency_grid <= max(y_min, y_max))
            )

        vertices = selection.get("vertices", [])
        if len(vertices) < 3:
            return np.zeros(self._stft.shape, dtype=bool)
        polygon = [(float(x), float(y)) for x, y in vertices]
        if self.frequency_scale == "log":
            polygon = [(x, _safe_log10_value(y)) for x, y in polygon]
        return _points_in_polygon(time_grid, frequency_grid, polygon)

    def _enabled_group_ids(self) -> set[str]:
        return {
            str(group.get("id"))
            for group in self.selection_groups
            if group.get("enabled", True)
        }

    def _selection_is_enabled(
        self, selection: dict[str, Any], enabled_group_ids: set[str]
    ) -> bool:
        if not self.selection_groups:
            return True
        group_id = selection.get("group_id")
        if group_id is None:
            group_id = self.selection_groups[0].get("id")
        return str(group_id) in enabled_group_ids

    def _has_enabled_selections(self) -> bool:
        enabled_group_ids = self._enabled_group_ids()
        return any(
            self._selection_is_enabled(selection, enabled_group_ids)
            for selection in self.selections
        )


def _default_selection_groups() -> list[dict[str, Any]]:
    return [
        {
            "id": "region-1",
            "name": "Region 1",
            "color": REGION_COLORS[0],
            "enabled": True,
        }
    ]


def _load_audio(audio: Any, sample_rate: int | None, *, mono: bool):
    import librosa
    import numpy as np

    if isinstance(audio, tuple) and len(audio) == 2:
        waveform, tuple_sample_rate = audio
        waveform = _array_audio(waveform, mono=mono)
        tuple_sample_rate = int(tuple_sample_rate)
        if sample_rate is not None and int(sample_rate) != tuple_sample_rate:
            waveform = librosa.resample(
                waveform,
                orig_sr=tuple_sample_rate,
                target_sr=int(sample_rate),
            )
            tuple_sample_rate = int(sample_rate)
        return waveform, tuple_sample_rate

    if isinstance(audio, (str, Path)):
        waveform, loaded_sample_rate = librosa.load(
            str(audio), sr=sample_rate, mono=mono
        )
        return _array_audio(waveform, mono=mono), int(loaded_sample_rate)

    if isinstance(audio, (bytes, bytearray)):
        waveform, loaded_sample_rate = librosa.load(
            BytesIO(audio), sr=sample_rate, mono=mono
        )
        return _array_audio(waveform, mono=mono), int(loaded_sample_rate)

    if hasattr(audio, "read"):
        if hasattr(audio, "seek"):
            audio.seek(0)
        waveform, loaded_sample_rate = librosa.load(audio, sr=sample_rate, mono=mono)
        return _array_audio(waveform, mono=mono), int(loaded_sample_rate)

    if sample_rate is None:
        raise ValueError(
            "sample_rate is required when audio is an array. Pass "
            "SoundSpectrograph((audio, sample_rate)) or sample_rate=... ."
        )

    waveform = _array_audio(np.asarray(audio, dtype=float), mono=mono)
    return waveform, int(sample_rate)


def _array_audio(audio: Any, *, mono: bool):
    import numpy as np

    waveform = np.asarray(audio, dtype=float)
    if waveform.size == 0:
        raise ValueError("audio must contain at least one sample.")
    if waveform.ndim == 1:
        return waveform
    if waveform.ndim != 2:
        raise ValueError("audio arrays must be one- or two-dimensional.")
    if not mono:
        raise ValueError("SoundSpectrograph currently expects mono audio.")
    if waveform.shape[0] <= waveform.shape[1]:
        return waveform.mean(axis=0)
    return waveform.mean(axis=1)


def _spectrogram_png_base64(
    values,
    *,
    width: int,
    height: int,
    colormap: str,
    db_range: float,
    frequency_scale: str = "linear",
    frequencies=None,
) -> str:
    import numpy as np

    values = np.asarray(values, dtype=float)
    max_value = float(np.nanmax(values))
    min_value = max_value - db_range
    normalized = np.clip((values - min_value) / db_range, 0, 1)
    normalized = np.nan_to_num(normalized, nan=0.0, posinf=1.0, neginf=0.0)

    row_idx = _spectrogram_row_indices(
        normalized.shape[0], height, frequency_scale=frequency_scale, frequencies=frequencies
    )
    col_idx = np.linspace(0, normalized.shape[1] - 1, width).astype(int)
    image_values = normalized[row_idx[:, None], col_idx]
    rgb = _apply_palette(image_values, PALETTES[colormap])
    return "data:image/png;base64," + base64.b64encode(_png_bytes(rgb)).decode("ascii")


def _spectrogram_row_indices(n_rows: int, height: int, *, frequency_scale: str, frequencies):
    import numpy as np

    if frequency_scale != "log" or frequencies is None:
        return np.linspace(n_rows - 1, 0, height).astype(int)

    frequencies = np.asarray(frequencies, dtype=float)
    positive = frequencies[frequencies > 0]
    if len(positive) == 0:
        return np.linspace(n_rows - 1, 0, height).astype(int)

    min_frequency = min(float(positive[0]), 1.0)
    max_frequency = max(float(frequencies[-1]), min_frequency)
    row_frequencies = np.geomspace(min_frequency, max_frequency, height)[::-1]
    row_idx = np.searchsorted(frequencies, row_frequencies)
    row_idx = np.clip(row_idx, 1, n_rows - 1)
    previous_idx = np.clip(row_idx - 1, 0, n_rows - 1)
    use_previous = np.abs(frequencies[previous_idx] - row_frequencies) < np.abs(
        frequencies[row_idx] - row_frequencies
    )
    return np.where(use_previous, previous_idx, row_idx).astype(int)


def _apply_palette(values, stops: list[tuple[float, tuple[int, int, int]]]):
    import numpy as np

    values = np.asarray(values, dtype=float)
    rgb = np.zeros(values.shape + (3,), dtype=np.uint8)
    for index, (left_position, left_color) in enumerate(stops[:-1]):
        right_position, right_color = stops[index + 1]
        span = right_position - left_position
        segment = (values >= left_position) & (values <= right_position)
        if span == 0:
            fraction = np.zeros_like(values)
        else:
            fraction = (values - left_position) / span
        for channel in range(3):
            rgb[..., channel] = np.where(
                segment,
                left_color[channel]
                + fraction * (right_color[channel] - left_color[channel]),
                rgb[..., channel],
            )
    return rgb


def _png_bytes(rgb) -> bytes:
    height, width, _ = rgb.shape

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + kind
            + data
            + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + row.tobytes() for row in rgb)
    return b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _points_in_polygon(x_values, y_values, polygon: list[tuple[float, float]]):
    import numpy as np

    x_values = np.asarray(x_values, dtype=float)
    y_values = np.asarray(y_values, dtype=float)
    inside = np.zeros(x_values.shape, dtype=bool)
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        crosses = (current_y > y_values) != (previous_y > y_values)
        slope_x = (previous_x - current_x) * (y_values - current_y) / (
            previous_y - current_y + 1e-12
        ) + current_x
        inside ^= crosses & (x_values < slope_x)
        previous_x, previous_y = current_x, current_y
    return inside


def _safe_log10(values):
    import numpy as np

    return np.log10(np.maximum(values, np.finfo(float).tiny))


def _safe_log10_value(value: float) -> float:
    import math

    return math.log10(max(float(value), 1e-300))


def _audio_wav_base64(audio, sample_rate: int) -> str:
    return "data:audio/wav;base64," + base64.b64encode(
        _audio_wav_bytes(audio, sample_rate)
    ).decode("ascii")


def _audio_wav_bytes(audio, sample_rate: int) -> bytes:
    import numpy as np

    audio = np.asarray(audio, dtype=float)
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    audio = np.clip(audio, -1.0, 1.0)
    samples = (audio * 32767).astype("<i2")
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())
    return buffer.getvalue()