"""Shared helpers for the audio-console control widgets (Knob, Fader).

Both widgets map a numeric value onto a track and let you draw an optional set
of ticks/axis labels. The tick spec is normalized here once, in Python, so the
frontend JS only ever has to draw a plain list of ``{"value", "label"}`` dicts.
"""

from typing import Any, Dict, List, Sequence, Union

# What a caller may pass for ``ticks``:
#   None / 0 / []            -> no ticks
#   an int N                 -> N evenly spaced ticks between min and max
#   [v1, v2, ...]            -> ticks at those values (labels are the values)
#   [(v1, "a"), (v2, "b")]   -> explicit value + label pairs
TickSpec = Union[None, int, Sequence[Union[float, Sequence[Any]]]]


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into ``[low, high]``."""
    return max(low, min(high, value))


def _format(value: float) -> str:
    """Render a tick value without trailing ``.0`` noise (12.0 -> "12")."""
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def normalize_ticks(
    ticks: TickSpec, min_value: float, max_value: float
) -> List[Dict[str, Any]]:
    """Turn a flexible ``ticks`` spec into a list of ``{"value", "label"}`` dicts.

    Args:
        ticks: See :data:`TickSpec` for the accepted forms.
        min_value: Lower bound of the value range (for the ``int`` count form).
        max_value: Upper bound of the value range (for the ``int`` count form).

    Returns:
        A list of ``{"value": float, "label": str}`` dicts, sorted by value.
        An empty list means "no ticks".
    """
    if ticks is None:
        return []

    # An int N (but not a bool) means "N evenly spaced ticks".
    if isinstance(ticks, int) and not isinstance(ticks, bool):
        if ticks <= 0:
            return []
        if ticks == 1:
            values = [min_value]
        else:
            span = max_value - min_value
            values = [min_value + span * i / (ticks - 1) for i in range(ticks)]
        return [{"value": float(v), "label": _format(v)} for v in values]

    out: List[Dict[str, Any]] = []
    for item in ticks:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            value = float(item)
            label = _format(value)
        else:
            # A (value, label) pair.
            try:
                raw_value, raw_label = item
            except (TypeError, ValueError):
                raise ValueError(
                    "Each tick must be a number or a (value, label) pair, "
                    f"got {item!r}."
                )
            value = float(raw_value)
            label = str(raw_label)
        out.append({"value": value, "label": label})

    out.sort(key=lambda t: t["value"])
    return out


def normalize_steps(steps: Sequence[Any]) -> List[float]:
    """Extract a sorted list of numeric stop values from a ``steps`` spec.

    Accepts the same shape as ticks — bare numbers or ``(value, label)`` pairs —
    but returns just the numeric positions the control should snap to. Requires
    at least two entries. Use together with :func:`normalize_ticks` (called on
    the same spec) to also get the labels for drawing.
    """
    values: List[float] = []
    for item in steps:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            values.append(float(item))
        else:
            try:
                raw_value, _label = item
            except (TypeError, ValueError):
                raise ValueError(
                    "Each step must be a number or a (value, label) pair, "
                    f"got {item!r}."
                )
            values.append(float(raw_value))
    if len(values) < 2:
        raise ValueError("Must pass at least two steps.")
    return sorted(values)
