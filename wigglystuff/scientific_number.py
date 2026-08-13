# pyright: reportExplicitAny = false, reportAny = false, reportPrivateImportUsage = false
"""Text-field numeric input that applies an arbitrary scale factor."""

from pathlib import Path
from typing import Any, Literal

import anywidget
import traitlets


def _num(**kwargs: Any) -> traitlets.Union:
    """A traitlet that accepts an int or a float without casting ints to floats."""
    return traitlets.Union([traitlets.Int(), traitlets.Float()], **kwargs)


def _snap(value: float, step: float) -> float:
    """Snap a value to an integer multiple of ``step``."""
    return round(value / step) * step


def _decimals(step: float) -> int:
    """Number of decimals implied by ``step``, used to keep snapping tidy."""
    text = repr(float(step))
    if "e" in text or "E" in text:
        return 12
    return len(text.split(".")[1].rstrip("0")) if "." in text else 0


_NOTATION_VALUES = ("decimal", "scientific")


def _finalize(
    raw: float,
    scale: float,
    step: float | None,
    min_scaled: float | None,
    max_scaled: float | None,
) -> float:
    """Snap *then* round *then* clamp a raw value against the scaled bounds.

    ``min_scaled``/``max_scaled`` are bounds on the scaled ``value``, so they
    are divided by ``scale`` before clamping the raw input. Rounding to the
    step's precision kills the floating point noise that ``_snap`` leaves
    behind (``round(2.002 / 0.001) * 0.001`` is ``2.0020000000000002``), and
    happens before clamping so bounds still hold.
    """
    if step:
        raw = _snap(raw, step)
        raw = round(raw, _decimals(step))
    else:
        raw = round(raw, 12)

    if min_scaled is not None:
        raw = max(raw, min_scaled / scale)
    if max_scaled is not None:
        raw = min(raw, max_scaled / scale)
    return raw


class ScientificNumber(anywidget.AnyWidget):
    """Text field for numbers that supports scientific notation, with an optional scale factor.

    Type ``5e+3`` or ``2.34e-8`` straight into the box — scientific notation
    parses natively. ``raw_value`` is the number you typed (after snapping and
    clamping); ``value`` is that number multiplied by ``scale``, the number you
    usually want in Python. ``scaled_value`` is an alias of ``value`` so the
    scaled number is readable directly off the wrapper
    (``mo.ui.anywidget(...).scaled_value``) without ``.value["value"]`` dict
    access. The ``value`` you pass to the constructor is the *scaled* value
    (what Python reads back), not the raw number shown in the box; omitting it
    starts the widget at ``0`` in both raw and scaled units.

    The widget renders as ``label | input | scale_label | unit_label``.
    ``label``, ``scale_label`` and ``unit_label`` are shown as plain text or
    ``$...$`` KaTeX. *``step`` snaps the raw input* to multiples of ``step``;
    since ``value`` is ``raw_value * scale``, that also puts ``value`` on
    multiples of ``step * scale``. ``min`` and ``max`` are bounds on the
    *scaled* ``value`` (``scale * raw_value``). ``scale`` and ``scale_label``
    are independent — you are responsible for keeping them consistent.

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import ScientificNumber

        number = mo.ui.anywidget(
            ScientificNumber(
                label="$\\text{Distance}$",
                unit_label="$\\text{m}$",
                scale=1e3,
                scale_label="$\\times 10^{3}$",
                value=2e3,
            )
        )
        number
        ```

        ```python
        mo.md(f"distance = {number.value['scaled_value']} {number.unit_label}")
        ```
    """

    _esm: Path = Path(__file__).parent / "static" / "scientific-number.js"
    _css: Path = Path(__file__).parent / "static" / "scientific-number.css"

    value: traitlets.Union = _num().tag(sync=True)
    raw_value: traitlets.Union = _num().tag(sync=True)
    scaled_value: traitlets.Union = _num().tag(sync=True)

    label: traitlets.Unicode[str, str | bytes] = traitlets.Unicode("").tag(sync=True)
    unit_label: traitlets.Unicode[str, str | bytes] = traitlets.Unicode("").tag(
        sync=True
    )
    scale: traitlets.Float[float, int | float] = traitlets.Float(1.0).tag(sync=True)
    scale_label: traitlets.Unicode[str, str | bytes] = traitlets.Unicode("").tag(
        sync=True
    )

    step: traitlets.Union = _num(default_value=None, allow_none=True).tag(sync=True)
    min: traitlets.Union = _num(default_value=None, allow_none=True).tag(sync=True)
    max: traitlets.Union = _num(default_value=None, allow_none=True).tag(sync=True)

    width: traitlets.Int[int, int] = traitlets.Int(300).tag(sync=True)
    inline_mode: traitlets.Bool[bool, bool | int] = traitlets.Bool(False).tag(sync=True)
    notation: traitlets.Unicode[str, str | bytes] = traitlets.Unicode("decimal").tag(
        sync=True
    )

    def __init__(
        self,
        label: str = "",
        unit_label: str = "",
        scale: float = 1.0,
        scale_label: str = "",
        step: float | None = None,
        min: float | None = None,
        max: float | None = None,
        value: float | None = None,
        width: int = 300,
        inline_mode: bool = False,
        notation: Literal["decimal", "scientific"] = "decimal",
        **kwargs: Any,
    ) -> None:
        """Create a ScientificNumber.

        Args:
            label: Optional label shown left of the box. Plain strings render as
                text; wrap in ``$...$`` to render KaTeX. Empty hides it.
            unit_label: Unit string shown in the right panel; plain text or
                ``$...$`` KaTeX.
            scale: Multiplier applied to the raw input to produce ``value``.
            scale_label: Text shown in the right panel for the scale; plain text
                or ``$...$`` KaTeX. This is display-only; keep it consistent
                with ``scale`` yourself.
            step: Optional snap increment, applied to the *raw* input. ``None``
                disables snapping. Because ``value`` is ``raw_value * scale``,
                the scaled value also lands on multiples of ``step * scale``.
            min: Lower bound on the scaled ``value``. ``None`` means unbounded.
            max: Upper bound on the scaled ``value``. ``None`` means unbounded.
            value: Initial *scaled* value — the number Python reads back,
                already multiplied by ``scale``, not the raw number shown in
                the box. Stored as ``raw_value`` after dividing by ``scale``
                and snapping/clamping. ``None`` (the default) starts the widget
                at ``0`` in both raw and scaled units.
            width: Widget width in pixels.
            inline_mode: Render compactly so the widget sits at text height
                inside a ``mo.md`` paragraph. Use ``.inline()`` for the same
                effect.
            notation: Display format for the value. ``"decimal"`` (default) or
                ``"scientific"``.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        # Guard `scale` before the division below; the trait validators cover
        # every other argument.
        if scale <= 0:
            raise traitlets.TraitError("scale must be positive.")

        raw = value / scale if value is not None else 0.0
        raw = _finalize(raw, scale, step, min, max)

        # Order matters: `value` is validated last, so it can read the already-set
        # scale/step/min/max traits instead of falling back to defaults.
        super().__init__(
            raw_value=raw,
            scale=scale,
            step=step,
            min=min,
            max=max,
            value=raw * scale,
            label=label,
            unit_label=unit_label,
            scale_label=scale_label,
            width=width,
            inline_mode=inline_mode,
            notation=notation,
            **kwargs,
        )

        # Keep the three numeric traits in sync: `value` is the scaled
        # number, `raw_value` the unscaled input, and `scaled_value` an alias
        # of `value` so the wrapper reads as `mo.ui.anywidget(...).scaled_value`
        # without going through the `.value["value"]` dict access.
        self.observe(self._sync_value, names=["raw_value", "scale"])
        self.observe(self._sync_raw_value, names="value")
        self.scaled_value = self.value
        self.observe(self._sync_scaled_value, names="value")
        self.observe(self._sync_value_from_scaled, names="scaled_value")

    def inline(self) -> "ScientificNumber":
        """Render compactly so the widget sits at text height in a paragraph.

        Lets the widget flow inside ``mo.md`` text (``mo.md(f"... {widget}
        ...")``) with the box hugging a single line of text instead of
        rendering as a full-height form field.
        """
        self.inline_mode = True
        return self

    @traitlets.validate("raw_value")
    def _validate_raw_value(self, proposal: traitlets.Bunch) -> float:
        scale = getattr(self, "scale", 1.0)
        return _finalize(
            proposal.value,
            scale,
            getattr(self, "step", None),
            getattr(self, "min", None),
            getattr(self, "max", None),
        )

    @traitlets.validate("value")
    def _validate_value(self, proposal: traitlets.Bunch) -> float:
        scale = getattr(self, "scale", 1.0)
        step = getattr(self, "step", None)
        raw = _finalize(
            proposal.value / scale,
            scale,
            step,
            getattr(self, "min", None),
            getattr(self, "max", None),
        )
        value = raw * scale
        # Clean the multiply noise (2.002 * 1000 == 2001.9999...) down to the
        # precision the step+scale actually imply. Without a step we have no
        # precision signal, so leave the raw product alone.
        if step:
            value = round(value, _decimals(step) + _decimals(scale))
        else:
            value = round(value, 12)

        return value

    @traitlets.validate("scale")
    def _validate_scale(self, proposal: traitlets.Bunch) -> float:
        if proposal.value <= 0:
            raise traitlets.TraitError("scale must be positive.")
        return proposal.value

    @traitlets.validate("step")
    def _validate_step(self, proposal: traitlets.Bunch) -> float | None:
        if proposal.value is not None and proposal.value <= 0:
            raise traitlets.TraitError("step must be positive.")
        return proposal.value

    @traitlets.validate("min", "max")
    def _validate_bounds(self, proposal: traitlets.Bunch) -> float | None:
        other = getattr(self, "max" if proposal.trait.name == "min" else "min", None)
        if proposal.value is not None and other is not None:
            lower, upper = (
                (proposal.value, other)
                if proposal.trait.name == "min"
                else (other, proposal.value)
            )
            if lower >= upper:
                raise traitlets.TraitError("min must be less than max.")
        return proposal.value

    @traitlets.validate("notation")
    def _validate_notation(self, proposal: traitlets.Bunch) -> str:
        if proposal.value not in _NOTATION_VALUES:
            raise traitlets.TraitError(f"notation must be one of {_NOTATION_VALUES}")
        return proposal.value

    def _sync_value(self, _: traitlets.Bunch) -> None:
        """Keep the scaled ``value`` in lockstep with ``raw_value``."""
        self.value = self.raw_value * self.scale

    def _sync_raw_value(self, change: traitlets.Bunch) -> None:
        """Mirror a Python-side ``value`` assignment back into the raw input."""
        self.raw_value = change["new"] / self.scale

    def _sync_scaled_value(self, change: traitlets.Bunch) -> None:
        """Keep the ``scaled_value`` alias in lockstep with ``value``."""
        self.scaled_value = change["new"]

    def _sync_value_from_scaled(self, change: traitlets.Bunch) -> None:
        """Mirror a ``scaled_value`` assignment back into ``value``."""
        self.value = change["new"]
