# Tangle Widgets API


## TangleSlider


 Bases: `AnyWidget`


Inline slider inspired by Bret Victor's Tangle UI.



```
from wigglystuff import Tangle Widgets

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
    super().__init__(value=choices[1], choices=choices, **kwargs)
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
