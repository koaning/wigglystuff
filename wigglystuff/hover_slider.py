from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

import anywidget
import traitlets


def _num() -> traitlets.Union:
    """A traitlet that accepts an int or a float without casting ints to floats."""
    return traitlets.Union([traitlets.Int(), traitlets.Float()])


def _is_number(value: Any) -> bool:
    # bool is a subclass of int and traitlets.Int() happily accepts it, so
    # reject it explicitly -- steps=[True, 2] is a mistake, not a slider.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_list(seq: Any) -> List[Any]:
    """Turn a sequence into a plain list, unwrapping numpy scalars along the way."""
    return seq.tolist() if hasattr(seq, "tolist") else list(seq)


def _infer_dtype(items: Sequence[Any]) -> type:
    """Mirror marimo's ``_infer_dtype``: float if anything is a float, else int."""
    return float if any(isinstance(x, float) for x in items if x is not None) else int


def _decimals(step: float) -> int:
    """Number of decimals implied by ``step``, used to keep snapping tidy."""
    text = repr(float(step))
    if "e" in text or "E" in text:
        return 12
    return len(text.split(".")[1].rstrip("0")) if "." in text else 0


def _cast(value: float, dtype: type) -> Union[int, float]:
    # round() before int(): JS sends 2.9999999999999996 where it means 3.
    return int(round(value)) if dtype is int else float(value)


def _snap_linear(
    value: float, start: float, stop: float, step: float, dtype: type
) -> Union[int, float]:
    value = max(start, min(stop, value))
    if step:
        value = start + round((value - start) / step) * step
        value = round(value, _decimals(step))
        value = max(start, min(stop, value))
    return _cast(value, dtype)


def _nearest(steps: Sequence[Any], value: float) -> Union[int, float]:
    """Closest entry in ``steps``, returned as the *stored* object.

    Returning the stored object (rather than a fresh float) is what keeps
    ``steps=[1, 2, 3]`` handing back an ``int``.
    """
    return min(steps, key=lambda s: abs(s - value))


class HoverSlider(anywidget.AnyWidget):
    """Horizontal slider that reports both a committed value and a live hover value.

    Hovering the track is an input channel of its own: ``hover_value`` follows the
    pointer while ``value`` stays parked where you last clicked. That lets a
    notebook preview a result before you commit to it. Click (or drag the puck) to
    move ``value``; when the pointer leaves the track ``hover_value`` falls back to
    ``value``, so it is never ``None``.

    Mirrors ``mo.ui.slider`` semantics: pass ``start``/``stop``/``step`` for a linear
    range, or ``steps`` for a list of discrete values (the two are mutually
    exclusive). Numeric types are preserved -- ``steps=[1, 2, 3]`` hands back an
    ``int``, ``steps=[1, 2.5, 4]`` hands back floats.

    Note:
        Hover fires a *lot*. Because ``mo.ui.anywidget`` reruns dependent cells on
        every synced trait change, ``sync_throttle_ms`` is the knob that decides how
        hard this widget hits your notebook: the default of 100ms caps it at roughly
        10 reruns per second while the pointer sweeps. Raise it if downstream cells
        are expensive; set it to ``0`` to sync every single pointer move.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import HoverSlider

        slider = mo.ui.anywidget(HoverSlider(start=0, stop=100, step=1, value=42))
        slider
        ```

        ```python
        # `hover_value` previews, `value` is what the user actually committed.
        mo.md(f"previewing {slider.value['hover_value']}, committed {slider.value['value']}")
        ```
    """

    _esm = Path(__file__).parent / "static" / "hover-slider.js"
    _css = Path(__file__).parent / "static" / "hover-slider.css"

    value = _num().tag(sync=True)
    hover_value = _num().tag(sync=True)
    hovering = traitlets.Bool(False).tag(sync=True)

    start = traitlets.Union([traitlets.Int(), traitlets.Float()], default_value=0).tag(
        sync=True
    )
    stop = traitlets.Union([traitlets.Int(), traitlets.Float()], default_value=100).tag(
        sync=True
    )
    # None in `steps` mode, mirroring mo.ui.slider.step.
    step = traitlets.Union(
        [traitlets.Int(), traitlets.Float()], default_value=1, allow_none=True
    ).tag(sync=True)
    # An empty list means linear mode, so JS can just test `steps.length`.
    steps = traitlets.List(_num(), default_value=[]).tag(sync=True)

    sync_throttle_ms = traitlets.Int(100).tag(sync=True)
    show_value = traitlets.Bool(True).tag(sync=True)
    label = traitlets.Unicode("").tag(sync=True)
    color = traitlets.Unicode("").tag(sync=True)
    width = traitlets.Int(400).tag(sync=True)

    def __init__(
        self,
        start: Optional[float] = None,
        stop: Optional[float] = None,
        step: Optional[float] = None,
        steps: Optional[Sequence[float]] = None,
        value: Optional[float] = None,
        sync_throttle_ms: int = 100,
        show_value: bool = True,
        label: str = "",
        color: str = "",
        width: int = 400,
        **kwargs: Any,
    ) -> None:
        """Create a HoverSlider.

        Args:
            start: Lower bound of the range. Defaults to ``0``.
            stop: Upper bound of the range. Defaults to ``100``.
            step: Snap increment (must be > 0). Defaults to ``1``.
            steps: List of discrete values to snap to, laid out evenly across the
                track regardless of spacing. Mutually exclusive with
                ``start``/``stop``/``step``. Needs at least two entries.
            value: Initial committed value; defaults to ``start`` (or ``steps[0]``).
                Snapped into range.
            sync_throttle_ms: Cap on how often hover/drag updates reach Python, in
                milliseconds. ``0`` syncs on every pointer move.
            show_value: Render the committed and hovered values as text below the track.
            label: Optional text label shown above the track. Empty string hides it.
            color: Optional CSS color (e.g. ``"#ef4444"``, ``"tomato"``) for the fill,
                puck border, and hover marker. Empty string uses the theme default.
            width: Widget width in pixels.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if steps is not None and (
            start is not None or stop is not None or step is not None
        ):
            raise ValueError(
                "Invalid arguments: `steps` is mutually exclusive with "
                "`start`, `stop`, and `step`."
            )

        if steps is not None:
            steps = _as_list(steps)
            if not all(_is_number(s) for s in steps):
                raise TypeError("Invalid steps: steps must be a sequence of numbers.")
            if len(steps) < 2:
                raise ValueError("Must pass at least two steps.")
            dtype = _infer_dtype(list(steps) + [value])
            steps = [_cast(s, dtype) for s in steps]
            value = steps[0] if value is None else _nearest(steps, value)
            start, stop, step = steps[0], steps[-1], None
        else:
            start = 0 if start is None else start
            stop = 100 if stop is None else stop
            step = 1 if step is None else step
            if not all(_is_number(x) for x in (start, stop, step)):
                raise TypeError("start, stop and step must be numbers.")
            if value is not None and not _is_number(value):
                raise TypeError("value must be a number.")
            if start >= stop:
                raise ValueError("start must be less than stop.")
            if step <= 0:
                raise ValueError("step must be positive.")
            dtype = _infer_dtype([start, stop, step, value])
            start, stop, step = (
                _cast(start, dtype),
                _cast(stop, dtype),
                _cast(step, dtype),
            )
            value = _snap_linear(
                start if value is None else value, start, stop, step, dtype
            )
            steps = []

        # Pass value *and* hover_value explicitly: traitlets skips cross-validation
        # for traits you leave at their class default.
        super().__init__(
            start=start,
            stop=stop,
            step=step,
            steps=steps,
            value=value,
            hover_value=value,
            hovering=False,
            sync_throttle_ms=sync_throttle_ms,
            show_value=show_value,
            label=label,
            color=color,
            width=width,
            **kwargs,
        )
        self.observe(self._mirror_hover_value, names="value")

    @traitlets.validate("value", "hover_value")
    def _snap_value(self, proposal: traitlets.Bunch) -> Union[int, float]:
        """Snap assignments from Python back into the slider's range and dtype.

        Deliberately reads only start/stop/step/steps -- during ``super().__init__``
        the two validated traits fire in an unspecified order, so this must not
        depend on ``self.value``.
        """
        value = proposal.value
        steps = getattr(self, "steps", None) or []
        if steps:
            return _nearest(steps, value)
        start = getattr(self, "start", 0)
        stop = getattr(self, "stop", 100)
        step = getattr(self, "step", 1) or 1
        return _snap_linear(value, start, stop, step, _infer_dtype([start, stop, step]))

    @traitlets.validate("sync_throttle_ms")
    def _validate_sync_throttle_ms(self, proposal: traitlets.Bunch) -> int:
        if proposal.value < 0:
            raise traitlets.TraitError("sync_throttle_ms must be non-negative.")
        return proposal.value

    def _mirror_hover_value(self, change: traitlets.Bunch) -> None:
        """Keep ``hover_value`` on ``value`` whenever the pointer isn't on the track."""
        if not self.hovering:
            self.hover_value = change["new"]
