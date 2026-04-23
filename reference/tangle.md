# Tangle Widgets API


## TangleSlider


 Bases: `AnyWidget`


Inline slider inspired by Bret Victor's Tangle UI.



```
from wigglystuff import Tangle Widgets

from wigglystuff import TangleSlider

slider = TangleSlider(amount=50, min_value=0, max_value=100)
slider
```


Create a slider suitable for inline Tangle interactions.


  Source code in `wigglystuff/tangle.py`

```
def __init__(
    self,
    amount: Optional[float] = None,
    min_value: float = -100,
    max_value: float = 100,
    step: float = 1.0,
    steps: Optional[List[float]] = None,
    pixels_per_step: int = 2,
    prefix: str = "",
    suffix: str = "",
    digits: int = 1,
    **kwargs: Any,
) -> None:
    """Create a slider suitable for inline Tangle interactions.

    Args:
        amount: Starting value; defaults to midpoint of bounds (linear mode)
            or first element (steps mode).
        min_value: Lower bound. Mutually exclusive with ``steps``.
        max_value: Upper bound. Mutually exclusive with ``steps``.
        step: Increment size. Mutually exclusive with ``steps``.
        steps: Explicit list of values to cycle through. When set,
            ``min_value``, ``max_value``, and ``step`` must not be provided.
        pixels_per_step: Drag distance per step.
        prefix: Text shown before the value.
        suffix: Text shown after the value.
        digits: Number formatting precision.
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if steps is not None:
        steps = [float(v) for v in steps]
        linear_given = {
            k for k, v in self._LINEAR_DEFAULTS.items()
            if locals()[k] != v
        }
        if linear_given:
            raise ValueError(
                f"Cannot use 'steps' together with {', '.join(sorted(linear_given))}."
            )
        if len(steps) < 2:
            raise ValueError("Must pass at least two steps.")
        if amount is not None and amount not in steps:
            raise ValueError(f"amount={amount} is not in the steps list.")
        if amount is None:
            amount = steps[0]
    else:
        steps = []
        if amount is None:
            amount = (max_value + min_value) / 2
    super().__init__(
        amount=amount,
        min_value=min_value,
        max_value=max_value,
        step=step,
        steps=steps,
        pixels_per_step=pixels_per_step,
        prefix=prefix,
        suffix=suffix,
        digits=digits,
        **kwargs,
    )
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `amount` | `float` | Current value. |
| `min_value` | `float` | Lower bound. |
| `max_value` | `float` | Upper bound. |
| `step` | `float` | Step size. |
| `pixels_per_step` | `int` | Drag distance per step. |
| `prefix` | `str` | Text before the value. |
| `suffix` | `str` | Text after the value. |
| `digits` | `int` | Decimal precision for display. |


## TangleChoice


 Bases: `AnyWidget`


Inline choice widget that cycles through labeled options.



```
from wigglystuff import Tangle Widgets

from wigglystuff import TangleChoice

choice = TangleChoice(choices=["small", "medium", "large"])
choice
```


Create a TangleChoice widget.


  Source code in `wigglystuff/tangle.py`

```
def __init__(self, choices: List[str], **kwargs: Any) -> None:
    """Create a TangleChoice widget.

    Args:
        choices: Ordered sequence of options (min two).
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if len(choices) < 2:
        raise ValueError("Must pass at least two choices.")
    super().__init__(choice=choices[0], choices=choices, **kwargs)
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |


## TangleSelect


 Bases: `AnyWidget`


Dropdown-based take on the Tangle choice pattern.



```
from wigglystuff import Tangle Widgets

from wigglystuff import TangleSelect

select = TangleSelect(choices=["red", "green", "blue"])
select
```


Create a TangleSelect dropdown.


  Source code in `wigglystuff/tangle.py`

```
def __init__(self, choices: List[str], **kwargs: Any) -> None:
    """Create a TangleSelect dropdown.

    Args:
        choices: Ordered sequence of options (min two).
        **kwargs: Forwarded to ``anywidget.AnyWidget``.
    """
    if len(choices) < 2:
        raise ValueError("Must pass at least two choices.")
    super().__init__(choice=choices[0], choices=choices, **kwargs)
```


### Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `choice` | `str` | Current selection. |
| `choices` | `list[str]` | Available options. |
