---
icon: lucide/rocket
---

# wigglystuff

**wigglystuff** is a collection of widgets that you can use in your Python notebooks. The primary target
for this work is [marimo](https://marimo.io), but because we are using [anywidget](https://anywidget.org) 
you should be able to use these tools in any Python notebook you like.

## Installation

```bash
uv pip install wigglystuff
```

## Usage

You simply import each widget to start using it. For marimo, we recommend wrapping 
each widget with `mo.ui.anywidget` to benefit most from the reactive environment. 

```python
import marimo as mo
from wigglystuff import Paint

widget = mo.ui.anywidget(Paint())
widget
```

## Features

We currently have the following widgets:

- `Paint`
- `EdgeDraw`
- `ColorPicker`
