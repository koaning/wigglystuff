# SoundSpectrograph API

::: wigglystuff.sound_spectrograph.SoundSpectrograph

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `spectrogram_base64` | `str` | Base64 PNG spectrogram rendered from the current audio. |
| `width` | `int` | Spectrogram canvas width in pixels. |
| `height` | `int` | Spectrogram canvas height in pixels. |
| `duration` | `float` | Audio duration in seconds. |
| `sample_rate` | `int` | Loaded sample rate. |
| `time_bounds` | `tuple[float, float]` | Time range shown on the x-axis. |
| `frequency_bounds` | `tuple[float, float]` | Frequency range shown on the y-axis. |
| `frequency_scale` | `str` | Frequency display scale: `"linear"` or `"log"`. |
| `colormap` | `str` | Rendered spectrogram palette: `"magma"`, `"viridis"`, or `"gray"`. |
| `mode` | `str` | Active selection mode: `"box"` or `"lasso"`. |
| `modes` | `list[str]` | Selection modes exposed in the toolbar. Defaults to `["box", "lasso"]`. |
| `selection_groups` | `list[dict]` | Region groups. Each group stores `id`, `name`, `color`, and `enabled`; disabled groups are ignored during display and playback reconstruction. |
| `active_group_index` | `int` | Region group that receives new selections. |
| `selections` | `list[dict]` | Persistent box/lasso selections. Box selections store `x_min`, `x_max`, `y_min`, and `y_max`; lasso selections store `vertices`; both store `type`, `id`, `color`, and `group_id`. Older selections without `group_id` belong to the first group. |
| `selected_index` | `int` | Active selection index, or `-1` when none is active. |
| `selection_opacity` | `float` | Fill opacity for selected regions. |
| `stroke_width` | `int` | Selection outline width in pixels. |
| `play_request_id` | `int` | Monotonic token incremented by the frontend to request reconstruction. |
| `selected_audio_base64` | `str` | Base64 WAV for the combined selected time-frequency bins. |
| `selected_audio_duration` | `float` | Duration of the reconstructed playback clip. |
| `is_playing` | `bool` | Browser playback state. |
| `playback_error` | `str` | Last playback preparation error. |
| `n_fft` | `int` | STFT window size. |
| `hop_length` | `int` | Samples between STFT frames. |
| `window` | `str` | Librosa STFT window name. |
| `power` | `float` | Magnitude exponent before decibel conversion. |

## Helper methods

| Method | Returns | Description |
| --- | --- | --- |
| `clear()` | `None` | Clear all selections and playback errors. |
| `add_selection_group(name=None, color=None, enabled=True)` | `dict` | Create a new region group and make it active. |
| `set_group_enabled(index, enabled)` | `None` | Toggle whether a region group contributes to display and playback. |
| `get_selection_mask()` | `ndarray[bool]` | Boolean mask over STFT bins covered by all selections. |
| `get_selected_audio(trim=True)` | `ndarray[float]` | Reconstruct audio from the combined selected bins, trimming to the selected time span by default. If there are no selections, returns the full loaded audio. |
| `save_selected_audio(path)` | `Path` | Save the selected reconstruction as a WAV file. |
| `set_audio(audio, sample_rate=None, mono=True)` | `None` | Replace the audio source and recompute the spectrogram. |