from pathlib import Path
from typing import Any, Dict, Optional

import anywidget
import traitlets


class Formula(anywidget.AnyWidget):
    """Interactive LaTeX formula widget with draggable numbers.

    Examples:
        ```python
        formula = Formula(
            formula=r"$x = {a} + {b}$",
            values={"a": 5, "b": 3},
            min_values={"a": 0, "b": 0},
            max_values={"a": 10, "b": 10}
        )
        formula
        ```
    """

    _esm = Path(__file__).parent / "static" / "formula.js"
    _css = Path(__file__).parent / "static" / "formula.css"
    formula = traitlets.Unicode("").tag(sync=True)
    values = traitlets.Dict({}).tag(sync=True)
    min_values = traitlets.Dict({}).tag(sync=True)
    max_values = traitlets.Dict({}).tag(sync=True)
    step_sizes = traitlets.Dict({}).tag(sync=True)
    digits = traitlets.Dict({}).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)

    def __init__(
        self,
        formula: str,
        values: Dict[str, float],
        min_values: Optional[Dict[str, float]] = None,
        max_values: Optional[Dict[str, float]] = None,
        step_sizes: Optional[Dict[str, float]] = None,
        digits: Optional[Dict[str, int]] = None,
        pixels_per_step: int = 2,
        **kwargs: Any,
    ) -> None:
        """Create a Formula widget with draggable numbers.

        Args:
            formula: LaTeX formula string with placeholders like {a}, {b}, etc.
            values: Dictionary mapping placeholder names to initial values.
            min_values: Optional dictionary mapping placeholder names to minimum values.
                       Defaults to -100 for all placeholders.
            max_values: Optional dictionary mapping placeholder names to maximum values.
                       Defaults to 100 for all placeholders.
            step_sizes: Optional dictionary mapping placeholder names to step sizes.
                       Defaults to 1.0 for all placeholders.
            digits: Optional dictionary mapping placeholder names to decimal precision.
                   Defaults to 1 for all placeholders.
            pixels_per_step: Number of pixels to drag per step increment.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        # Extract placeholder names from formula
        import re
        placeholders = set(re.findall(r'\{(\w+)\}', formula))
        
        if not placeholders:
            raise ValueError("Formula must contain at least one placeholder like {a}, {b}, etc.")
        
        if set(values.keys()) != placeholders:
            raise ValueError(
                f"Values keys {set(values.keys())} must match placeholders {placeholders} in formula"
            )
        
        # Set defaults for optional parameters
        if min_values is None:
            min_values = {k: -100.0 for k in placeholders}
        else:
            min_values = {k: min_values.get(k, -100.0) for k in placeholders}
        
        if max_values is None:
            max_values = {k: 100.0 for k in placeholders}
        else:
            max_values = {k: max_values.get(k, 100.0) for k in placeholders}
        
        if step_sizes is None:
            step_sizes = {k: 1.0 for k in placeholders}
        else:
            step_sizes = {k: step_sizes.get(k, 1.0) for k in placeholders}
        
        if digits is None:
            digits = {k: 1 for k in placeholders}
        else:
            digits = {k: digits.get(k, 1) for k in placeholders}
        
        # Validate values are within bounds
        for k, v in values.items():
            if v < min_values[k]:
                raise ValueError(f"Value {v} for '{k}' is less than min_value {min_values[k]}")
            if v > max_values[k]:
                raise ValueError(f"Value {v} for '{k}' is greater than max_value {max_values[k]}")
        
        super().__init__(
            formula=formula,
            values=values,
            min_values=min_values,
            max_values=max_values,
            step_sizes=step_sizes,
            digits=digits,
            pixels_per_step=pixels_per_step,
            **kwargs,
        )
