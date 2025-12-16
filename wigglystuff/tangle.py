from pathlib import Path
from typing import Any, List, Optional

import anywidget
import traitlets


class TangleSlider(anywidget.AnyWidget):
    """Inline slider inspired by Bret Victor's Tangle UI.

    Examples:
        ```python
        slider = TangleSlider(amount=50, min_value=0, max_value=100)
        slider
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-slider.js"
    amount = traitlets.Float(0.0).tag(sync=True)
    min_value = traitlets.Float(-100.0).tag(sync=True)
    max_value = traitlets.Float(100.0).tag(sync=True)
    step = traitlets.Float(1.0).tag(sync=True)
    pixels_per_step = traitlets.Int(2).tag(sync=True)
    prefix = traitlets.Unicode("").tag(sync=True)
    suffix = traitlets.Unicode("").tag(sync=True)
    digits = traitlets.Int(1).tag(sync=True)

    def __init__(
        self,
        amount: Optional[float] = None,
        min_value: float = -100,
        max_value: float = 100,
        step: float = 1.0,
        pixels_per_step: int = 2,
        prefix: str = "",
        suffix: str = "",
        digits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Create a slider suitable for inline Tangle interactions.

        Args:
            amount: Starting value; defaults to midpoint of bounds.
            min_value: Lower bound.
            max_value: Upper bound.
            step: Increment size.
            pixels_per_step: Drag distance per step.
            prefix: Text shown before the value.
            suffix: Text shown after the value.
            digits: Number formatting precision.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if amount is None:
            amount = (max_value + min_value) / 2
        super().__init__(
            amount=amount,
            min_value=min_value,
            max_value=max_value,
            step=step,
            pixels_per_step=pixels_per_step,
            prefix=prefix,
            suffix=suffix,
            digits=digits,
            **kwargs,
        )


class TangleChoice(anywidget.AnyWidget):
    """Inline choice widget that cycles through labeled options.

    Examples:
        ```python
        choice = TangleChoice(choices=["small", "medium", "large"])
        choice
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-choice.js"
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs: Any) -> None:
        """Create a TangleChoice widget.

        Args:
            choices: Ordered sequence of options (min two).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(value=choices[1], choices=choices, **kwargs)


class TangleSelect(anywidget.AnyWidget):
    """Dropdown-based take on the Tangle choice pattern.

    Examples:
        ```python
        select = TangleSelect(choices=["red", "green", "blue"])
        select
        ```
    """

    _esm = Path(__file__).parent / "static" / "tangle-select.js"
    choice = traitlets.Unicode("").tag(sync=True)
    choices = traitlets.List([]).tag(sync=True)

    def __init__(self, choices: List[str], **kwargs: Any) -> None:
        """Create a TangleSelect dropdown.

        Args:
            choices: Ordered sequence of options (min two).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if len(choices) < 2:
            raise ValueError("Must pass at least two choices.")
        super().__init__(choice=choices[0], choices=choices, **kwargs)
