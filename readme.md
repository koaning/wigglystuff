# wigglystuff 

> "A collection of expressive Jupyter widgets."
 
<img src="imgs/logo.png" width=125 height=125 align="right" style="z-index: 9999;">

This small Python library contains Jupyter widgets that allow you to draw a dataset in a Jupyter
notebook. This should be very useful when teaching machine learning algorithms.

![](imgs/widget.gif)

The project uses [anywidget](https://anywidget.dev/) under the hood so our tools should work in Jupyter, VSCode and Colab. That also means that you get a proper widget that can interact with [ipywidgets](https://ipywidgets.readthedocs.io/en/stable/) natively. [Here](https://www.youtube.com/watch?v=STPv0jSAQEk) is an example where updating a drawing triggers a new scikit-learn model to train ([code](https://github.com/probabl-ai/youtube-appendix/blob/main/04-drawing-data/notebook.ipynb)).

![](imgs/update.gif)

You can really get creative with this in a notebook, so feel free to give it a spin!

## Installation 

Installation occurs via pip. 

```
python -m pip install wigglystuff
```

## Usage

There are a bunch of widgets that this library provides that could be useful. The sections below will highlight each of them.

### `Slider2D`

```python
from wigglystuff import Slider2D

widget = Slider2D()
widget
```

![](imgs/slider2d.gif)
