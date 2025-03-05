from typing import List
from pathlib import Path
import anywidget
import traitlets


class Slider2D(anywidget.AnyWidget):
    """Initialize a Slider2D widget.

    Args:
        x: Initial x coordinate value. Defaults to 0.
        y: Initial y coordinate value. Defaults to 0.
        width: Width of the slider widget in pixels. Defaults to 400.
        height: Height of the slider widget in pixels. Defaults to 400.
        **kwargs: Additional keyword arguments passed to parent class.
    """
    _esm = Path(__file__).parent / 'static' / '2dslider.js'
    x = traitlets.Float(0.0).tag(sync=True)
    y = traitlets.Float(0.0).tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)

    def __init__(self, x: float = 0, y: float = 0, width: int = 400, height: int = 400, **kwargs) -> None:
        super().__init__(x=x, y=y, width=width, height=height, **kwargs)


class Matrix(anywidget.AnyWidget):
    """Initialize a Matrix widget.

    Args:
        matrix: Optional 2D list of values to initialize the matrix with.
                If None, matrix will be initialized with mean of min/max values.
        rows: Number of rows in the matrix.
        cols: Number of columns in the matrix.
        min_value: Minimum allowed value in the matrix.
        max_value: Maximum allowed value in the matrix.
        triangular: If True, only allow editing upper triangle of matrix.
        **kwargs: Additional keyword arguments passed to parent class.
    """
    _esm = Path(__file__).parent / 'static' / 'matrix.js'
    _css = Path(__file__).parent / 'static' / 'matrix.css'
    matrix = traitlets.List([]).tag(sync=True)
    rows = traitlets.Int(3).tag(sync=True)
    cols = traitlets.Int(3).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    mirror = traitlets.Bool(False).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)

    def __init__(self, matrix: List[List[float]] | None = None, 
                 rows: int = 3, 
                 cols: int = 3, 
                 min_value: float = -100, 
                 max_value: float = 100, 
                 triangular: bool = False, 
                 **kwargs) -> None:
        if matrix is not None:
            import numpy as np
            matrix = np.array(matrix)
            if matrix.min() < min_value:
                raise ValueError(f"The min value of input matrix is less than min_value={min_value}.")
            if matrix.max() > max_value:
                raise ValueError(f"The max value of input matrix is less than max_value={max_value}.")
            rows, cols = matrix.shape
            matrix = matrix.tolist()
        else:
            matrix = [[(min_value + max_value) / 2 for i in range(cols)] for j in range(rows)]
        super().__init__(matrix=matrix, rows=rows, cols=cols, triangular=triangular, **kwargs)


class TangleSlider(anywidget.AnyWidget):
    """Initialize a TangleSlider widget.

    Args:
        amount: Initial value of the slider. If None, uses mean of min/max.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        step: Step size for value changes.
        pixels_per_step: Number of pixels per step when dragging.
        prefix: Text to display before the value.
        suffix: Text to display after the value.
        digits: Number of decimal places to display.
        **kwargs: Additional keyword arguments passed to parent class.
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-slider.js'
    amount = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)
    prefix = traitlets.Unicode("").tag(sync=True)
    suffix = traitlets.Unicode("").tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)

    def __init__(self, 
                 amount: float | None = None,
                 min_value: float = -100,
                 max_value: float = 100,
                 step: float = 1.0,
                 pixels_per_step: int = 2,
                 prefix: str = "",
                 suffix: str = "",
                 digits: int = 1,
                 **kwargs) -> None:
        if amount is None:
            amount = (max_value + min_value)/2
        super().__init__(amount=amount, min_value=min_value, max_value=max_value, step=step, pixels_per_step=pixels_per_step, prefix=prefix, suffix=suffix, digits=digits, **kwargs)


class TangleChoice(anywidget.AnyWidget):
    """Initialize a TangleChoice widget.

    Args:
        choices: List of at least two string choices to select from.
        **kwargs: Additional keyword arguments passed to parent class.

    Raises:
        ValueError: If fewer than two choices are provided.
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-choice.js'
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs) -> None:
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(value=choices[1], choices=choices, **kwargs)


class EdgeDraw(anywidget.AnyWidget):
    """Initialize a EdgeDraw widget.

    Args:
        names: List of names for the nodes.
    """
    _esm = Path(__file__).parent / 'static' / 'edgedraw.js'
    _css = Path(__file__).parent / 'static' / 'edgedraw.css'
    names = traitlets.List([]).tag(sync=True)
    links = traitlets.List([]).tag(sync=True)
    
    def __init__(self, names: List[str]) -> None:
        super().__init__(names=names)


class TangleSelect(anywidget.AnyWidget):
    """Initialize a TangleSelect widget.

    Args:
        choices: List of at least two string choices to select from in a dropdown.
        **kwargs: Additional keyword arguments passed to parent class.

    Raises:
        ValueError: If fewer than two choices are provided.
    """
    _esm = Path(__file__).parent / 'static' / 'tangle-select.js'
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs) -> None:
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(choice=choices[0], choices=choices, **kwargs)


class CopyToClipboard(anywidget.AnyWidget):
    """Initialize a CopyToClipboard widget.

    Args:
        text_to_copy: String to copy to the clipboard when button is pressed.
    """
    text_to_copy = traitlets.Unicode("").tag(sync=True)
    
    _esm = """
    function render({ model, el }) {
        // Create a button element
        const button = document.createElement("button");
        button.textContent = "Copy to Clipboard";
        
        // Add a click event listener to the button
        button.addEventListener("click", async () => {
            try {
                // Copy the text to the clipboard
                await navigator.clipboard.writeText(model.get("text_to_copy"));
                console.log("Text copied to clipboard:", model.get("text_to_copy"));
            } catch (err) {
                console.error("Failed to copy text:", err);
            }
        });
        
        // Append the button to the widget's element
        el.appendChild(button);
    };
    
    export default {render};
    """
    
    def __init__(self, text_to_copy="", **kwargs):
        super().__init__(**kwargs)
        self.text_to_copy = text_to_copy
