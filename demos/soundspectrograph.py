# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "librosa>=0.10.0",
#     "marimo",
#     "numpy",
#     "wigglystuff==0.5.7",
# ]
# ///

import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    import sys

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import marimo as mo
    import numpy as np
    from wigglystuff import SoundSpectrograph

    return Path, SoundSpectrograph, mo


@app.cell
def _(Path, SoundSpectrograph, mo):
    audio_path = Path("/path/to/file.mp3") # also supports WAV, OGG, FLAC, etc. (any format supported by librosa)

    spectrograph = mo.ui.anywidget(
        SoundSpectrograph(
        audio_path,
        sample_rate=None,          # preserve WAV sample rate
        mono=True,                 # downmix stereo/multichannel
        n_fft=4096,                # detailed frequency view
        hop_length=512,            # good playback/selection responsiveness
        # frequency_scale="log",     # better for speech/music perception
        colormap="magma",          # "magma", "viridis", or "gray"
        width=1050,
        height=420,
        selection_opacity=0.28,
        )
    )

    spectrograph
    return (spectrograph,)


@app.cell
def _(spectrograph):
    spectrograph.selections
    return


@app.cell
def _(spectrograph):
    spectrograph.selected_audio_duration, spectrograph.playback_error
    return


if __name__ == "__main__":
    app.run()
