# wigglystuff 

<img src="imgs/stuff.png" width=125 height=125 align="right" style="z-index: 9999;">

> "A collection of creative AnyWidgets for Python notebook environments."

The project uses [anywidget](https://anywidget.dev/) under the hood so our tools should work in [marimo](https://marimo.io/), [Jupyter](https://jupyter.org/), [Shiny for Python](https://shiny.posit.co/py/docs/jupyter-widgets.html), [VSCode](https://code.visualstudio.com/docs/datascience/jupyter-notebooks), [Colab](https://colab.google/), [Solara](https://solara.dev/), etc. Because of the anywidget integration you should also be able interact with [ipywidgets](https://ipywidgets.readthedocs.io/en/stable/) natively. 

## Widget Gallery

For full documentation, visit [wigglystuff.dev](https://wigglystuff.dev).

<table>
<tr>
<td align="center"><b>Slider2D</b><br><a href="https://wigglystuff.dev/reference/slider2d/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/slider2d.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/slider2d/">Demo</a> · <a href="https://wigglystuff.dev/reference/slider2d/">API</a></td>
<td align="center"><b>Matrix</b><br><a href="https://wigglystuff.dev/reference/matrix/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/matrix.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/matrix/">Demo</a> · <a href="https://wigglystuff.dev/reference/matrix/">API</a></td>
<td align="center"><b>Paint</b><br><a href="https://wigglystuff.dev/reference/paint/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/paint.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/paint/">Demo</a> · <a href="https://wigglystuff.dev/reference/paint/">API</a></td>
</tr>
<tr>
<td align="center"><b>EdgeDraw</b><br><a href="https://wigglystuff.dev/reference/edge-draw/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/edgedraw.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/edgedraw/">Demo</a> · <a href="https://wigglystuff.dev/reference/edge-draw/">API</a></td>
<td align="center"><b>SortableList</b><br><a href="https://wigglystuff.dev/reference/sortable-list/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/sortablelist.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/sortlist/">Demo</a> · <a href="https://wigglystuff.dev/reference/sortable-list/">API</a></td>
<td align="center"><b>ColorPicker</b><br><a href="https://wigglystuff.dev/reference/color-picker/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/colorpicker.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/colorpicker/">Demo</a> · <a href="https://wigglystuff.dev/reference/color-picker/">API</a></td>
</tr>
<tr>
<td align="center"><b>GamepadWidget</b><br><a href="https://wigglystuff.dev/reference/gamepad/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/gamepad.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/gamepad/">Demo</a> · <a href="https://wigglystuff.dev/reference/gamepad/">API</a></td>
<td align="center"><b>KeystrokeWidget</b><br><a href="https://wigglystuff.dev/reference/keystroke/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/keystroke.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/keystroke/">Demo</a> · <a href="https://wigglystuff.dev/reference/keystroke/">API</a></td>
<td align="center"><b>SpeechToText</b><br><a href="https://wigglystuff.dev/reference/talk/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/speechtotext.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/talk/">Demo</a> · <a href="https://wigglystuff.dev/reference/talk/">API</a></td>
</tr>
<tr>
<td align="center"><b>CopyToClipboard</b><br><a href="https://wigglystuff.dev/reference/copy-to-clipboard/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/copytoclipboard.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/copytoclipboard/">Demo</a> · <a href="https://wigglystuff.dev/reference/copy-to-clipboard/">API</a></td>
<td align="center"><b>CellTour</b><br><a href="https://wigglystuff.dev/reference/cell-tour/"><img src="https://raw.githubusercontent.com/koaning/wigglystuff/main/mkdocs/assets/gallery/celltour.png" width="200"></a><br><a href="https://wigglystuff.dev/examples/celltour/">Demo</a> · <a href="https://wigglystuff.dev/reference/cell-tour/">API</a></td>
<td align="center"></td>
</tr>
</table>

## Online demos

We've made some demos of the widgets and shared them on the Marimo gallery for easy exploration.

<table>
<tr>
<td align="center">
    <a href="https://marimo.io/p/@marimo/interactive-matrices">
        <b>Matrix demo with PCA</b>
    </a>
</td>
<td align="center">
    <a href="https://marimo.io/p/@vincent-d-warmerdam-/tangle-demo">
        <b>Tangle Widgets for exploration</b>
    </a>
</td>
</tr><tr>
<td align="center">
    <a href="https://marimo.io/p/@marimo/interactive-matrices">
        <img src="https://marimo.io/_next/image?url=%2Fimages%2Fgallery%2Finteractive-matrices.gif&w=1080&q=75" width="290"><br>
    </a>
</td>
<td align="center">
    <a href="https://marimo.io/p/@vincent-d-warmerdam-/tangle-demo">
        <img src="https://marimo.io/_next/image?url=%2Fimages%2Fgallery%2Ftangle.gif&w=1080&q=75" width="290"><br>
    </a>
</td>
</tr>
</table>

## Installation 

Installation occurs via `pip` or `uv`. We prefer `uv`. 

```
uv pip install wigglystuff
```

To install all development requirements (tests, docs, JavaScript tooling), run:

```
make install
```

## Documentation

Install the optional extras and launch MkDocs Material to preview the new site with embedded Marimo demos:

```
uv pip install -e '.[docs]'
make docs
```

Run `make docs-demos` whenever you need to refresh the html-wasm exports from `demos/*.py`, then `make docs-serve` if you want the live-reload server. `make docs-build` chains the export + build steps for deploys.

## Usage

### `Slider2D`

```python
from wigglystuff import Slider2D

widget = Slider2D()
widget
```

![](imgs/slider2d.gif)

This widget allows you to grab the `widget.x` and `widget.y` properties to get the current position of the slider. But you can also use the `widget.observe` method to listen to changes in the widget. 

<details>
<summary><b>Example of <code>widget.observe</code></b></summary>

```python
import ipywidgets
from wigglystuff import Slider2D

widget = Slider2D()
output = ipywidgets.Output()
state = [[0.0, 0.0]]

@output.capture(clear_output=True)
def on_change(change):
    if abs(widget.x - state[-1][0]) > 0.01:
        if abs(widget.y - state[-1][1]) > 0.01:
            state.append([widget.x, widget.y])
    for elem in state[-5:]:
        print(elem)

widget.observe(on_change)
on_change(None)
ipywidgets.HBox([widget, output])
```
</details>

### `Matrix`

If you want to get an intuition of linear algebra, the `Matrix` object might really help. It can generate a matrix for you that allows you to update all the values in it. 

```python
from wigglystuff import Matrix

arr = Matrix(rows=1, cols=2, step=0.1)
mat = Matrix(matrix=np.eye(2), mirror=True, step=0.1)
```

![](imgs/matix.gif)

### `TangleSlider` 

Sliders are neat, but maybe you'd prefer to have something more inline. For that use-case the `TangleSlider` can be just what you need. 

```python
from wigglystuff import TangleSlider
```

![](imgs/tangleslider.gif)

### `TangleChoice` & `TangleSelect`

This is similar to the `TangleSlider` but for discrete choices. 

```python
from wigglystuff import TangleChoice
```

![](imgs/tanglechoice.gif)

`TangleSelect` is just like `TangleChoice` but with a dropdown.

```python
from wigglystuff import TangleSelect
```

### `CopyToClipboard` 

This is a simple button, but one that allows you to copy anything of interest
to the clipboard. This can be very helpful for some interactive Marimo apps where
the output needs to be copied into another app. 

```python
from wigglystuff import CopyToClipboard

CopyToClipboard("this can be copied")
```

### `ColorPicker`

This is a base HTML color picker, ready for use in a notebook. 

```python
from wigglystuff import ColorPicker

ColorPicker()
```

### `KeystrokeWidget`

Capture the latest keyboard shortcut pressed inside a notebook cell. The widget stores the last key event (including modifier state) in the `last_key` trait so you can respond to shortcuts in Python.

```python
from wigglystuff import KeystrokeWidget

keyboard = KeystrokeWidget()
keyboard
keyboard.last_key  # => {"key": "K", "ctrlKey": True, ...}
```

### `SortableList`

An interactive drag-and-drop sortable list widget. By default, it's just sortable, but you can enable additional features as needed.

```python
from wigglystuff import SortableList

# Just sortable (default)
SortableList(["Action", "Comedy", "Drama", "Thriller"])

# Full-featured todo list
SortableList(["Task 1", "Task 2"], addable=True, removable=True, editable=True)

# Edit-only mode
SortableList(["Click to edit me"], editable=True)
```

### `WebkitSpeechToTextWidget`

This widget wraps the browser's Webkit Speech API so you can dictate text directly into Python notebooks without dealing with API keys. It exposes two traits: `transcript` for the current text and `listening` so you can start or stop recording from Python if you prefer.

```python
from wigglystuff import WebkitSpeechToTextWidget

widget = WebkitSpeechToTextWidget()
widget

# Access the transcript at any time
widget.transcript
```

### `Paint`

A port of the [mopaint](https://github.com/koaning/mopaint) widget that offers simple MS Paint style sketching straight from a notebook. You can start with an empty canvas or load an existing image and later export the result as a PIL image or base64 string.

```python
from wigglystuff import Paint

canvas = Paint(height=400)
canvas
```

## Development

I am currently exploring how we might move some of these components to react, mainly in an attempt to keep things flexible in the future. There's no need to port everything just yet but I have ported the clipboard button. You should be able to develop it via: 

```
npm run dev-copy-btn
```

This assumes that you ran `npm install` beforehand. 
