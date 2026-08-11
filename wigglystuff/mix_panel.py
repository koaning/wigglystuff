from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Union

import anywidget
import traitlets

from ._controls import widget_refs


_ESM_PATH = Path(__file__).parent / "static" / "mix-panel.js"
_CSS_PATH = Path(__file__).parent / "static" / "mix-panel.css"

Controls = Union[Mapping[str, Any], Sequence[Any]]


class MixPanel(anywidget.AnyWidget):
    """A rack of child control widgets (Knobs and Faders) laid out as channel strips.

    MixPanel is a true *nested* anywidget: the child widgets are mounted inside
    the panel's own view via anywidget's widget-composition host (requires
    ``anywidget>=0.11.0`` and a host that implements it, e.g. marimo or
    Jupyter). Each child still syncs its own ``value`` as usual; MixPanel also
    aggregates them into a combined ``values`` dict keyed by name.

    Pass either a mapping of ``{name: widget}`` or a list of widgets (names are
    taken from each widget's ``label``, falling back to ``"channel N"``).

    Examples:
        ```python
        import marimo as mo
        from wigglystuff import MixPanel, Knob, Fader

        panel = mo.ui.anywidget(MixPanel({
            "gain": Knob(min_value=0, max_value=11, value=5, label="Gain"),
            "level": Fader(min_value=-60, max_value=6, value=0, label="Level"),
        }, title="Channel 1"))
        panel
        ```

        Read the aggregated values back with ``panel.values`` ->
        ``{"gain": 5.0, "level": 0.0}``.
    """

    _esm = _ESM_PATH
    _css = _CSS_PATH

    controls = traitlets.List().tag(sync=True, to_json=widget_refs)
    names = traitlets.List(traitlets.Unicode()).tag(sync=True)
    values = traitlets.Dict().tag(sync=True)
    title = traitlets.Unicode("").tag(sync=True)
    width = traitlets.Int(0).tag(sync=True)

    def __init__(
        self,
        controls: Controls,
        title: str = "",
        width: int = 0,
        **kwargs: Any,
    ) -> None:
        """Create a MixPanel.

        Args:
            controls: Either a ``{name: widget}`` mapping or a list of control
                widgets. With a list, each name comes from the widget's
                ``label`` (falling back to ``"channel N"``).
            title: Optional title shown above the rack.
            width: Optional fixed panel width in pixels (0 = size to content).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if isinstance(controls, Mapping):
            names = [str(name) for name in controls.keys()]
            widgets = list(controls.values())
        else:
            widgets = list(controls)
            names = [
                getattr(w, "label", "") or f"channel {i + 1}"
                for i, w in enumerate(widgets)
            ]

        if len(set(names)) != len(names):
            raise ValueError(f"control names must be unique, got {names}.")

        self._widgets: List[Any] = widgets
        self._names: List[str] = names
        super().__init__(
            controls=widgets,
            names=names,
            values={name: _child_value(w) for name, w in zip(names, widgets)},
            title=title,
            width=width,
            **kwargs,
        )

        # Aggregate each child's value into the combined dict. Done in Python so
        # the {name: value} view works regardless of frontend host support.
        for widget in widgets:
            observed = _value_traits(widget)
            if observed:
                widget.observe(self._sync_values, names=observed)

    def _sync_values(self, _change: Dict[str, Any]) -> None:
        self.values = {
            name: _child_value(w) for name, w in zip(self._names, self._widgets)
        }


def _value_traits(widget: Any) -> List[str]:
    """Which traits carry this child's "value" (so we know what to observe)."""
    if widget.has_trait("value"):
        return ["value"]
    return [t for t in ("x", "y") if widget.has_trait(t)]


def _child_value(widget: Any) -> Any:
    """The child's current value: ``value`` if it has one, else an ``(x, y)`` pair."""
    if widget.has_trait("value"):
        return widget.value
    if widget.has_trait("x") and widget.has_trait("y"):
        return (widget.x, widget.y)
    return None
