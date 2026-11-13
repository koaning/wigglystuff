"""Shape-only displays for NumPy arrays in marimo notebooks."""

from __future__ import annotations

from html import escape
from typing import Any
from uuid import uuid4


_SHAPE_DISPLAY_TYPE = None


def _normalize_labels(labels, ndim):
    if labels is None:
        return (None,) * ndim

    labels = tuple(labels)
    if len(labels) != ndim:
        raise ValueError(
            "labels must have one entry per array axis; "
            f"got {len(labels)} entries for a {ndim}D array"
        )
    if any(part is not None and not isinstance(part, str) for part in labels):
        raise TypeError("labels must be strings or None")
    if any(part == "" for part in labels):
        raise ValueError("labels cannot be empty strings")
    return labels


def _caption_html(array) -> str:
    parts = []
    for label, size in zip(array.labels, array.shape):
        if label is None:
            parts.append(f'<span class="ws-shape-display-size">{size}</span>')
        else:
            parts.append(f"<var>{escape(label)}</var>")
    return '<span class="ws-shape-display-times"> × </span>'.join(parts)


def _planes_svg(ndim: int, uid: str) -> str:
    if ndim == 2:
        return """
        <svg viewBox="0 0 76 62" width="76" height="62" aria-hidden="true">
          <path d="M25 5H14v52h11 M51 5h11v52H51" />
        </svg>
        """

    # The three bracket pairs act like sheets of paper: a sheet hides
    # everything behind it, so each plane only shows where it sticks out
    # past the sheet in front of it — no strokes ever blend. The occluding
    # rects are the sheets' outlines grown by half the stroke width (2.5/2),
    # so a farther plane emerges exactly at the nearer plane's outer edge
    # instead of showing through its translucent stroke.
    return f"""
    <svg viewBox="0 0 96 76" width="96" height="76" aria-hidden="true">
      <defs>
        <mask id="ws-shape-display-back-{uid}" maskUnits="userSpaceOnUse"
              x="0" y="0" width="96" height="76">
          <rect x="0" y="0" width="96" height="76" fill="white" />
          <rect x="19.75" y="10.75" width="50.5" height="54.5" fill="black" />
          <rect x="12.75" y="17.75" width="50.5" height="54.5" fill="black" />
        </mask>
        <mask id="ws-shape-display-middle-{uid}" maskUnits="userSpaceOnUse"
              x="0" y="0" width="96" height="76">
          <rect x="0" y="0" width="96" height="76" fill="white" />
          <rect x="12.75" y="17.75" width="50.5" height="54.5" fill="black" />
        </mask>
      </defs>
      <g class="ws-shape-display-plane ws-shape-display-plane-back"
         mask="url(#ws-shape-display-back-{uid})">
        <path d="M39 5H28v52h11 M65 5h11v52H65" />
      </g>
      <g class="ws-shape-display-plane ws-shape-display-plane-middle"
         mask="url(#ws-shape-display-middle-{uid})">
        <path d="M32 12H21v52h11 M58 12h11v52H58" />
      </g>
      <g class="ws-shape-display-plane ws-shape-display-plane-front">
        <path d="M25 19H14v52h11 M51 19h11v52H51" />
      </g>
    </svg>
    """


def _strip_math_delimiters(name: str) -> str:
    for left, right in (("$$", "$$"), ("$", "$"), (r"\(", r"\)"), (r"\[", r"\]")):
        if len(name) >= 2 * len(left) and name.startswith(left) and name.endswith(right):
            return name[len(left):len(name) - len(right)].strip()
    return name


def _is_tex(name: str) -> bool:
    return "\\" in name or name.startswith("$")


_TEXT_ESCAPES = {
    "\\": r"\textbackslash{}", "_": r"\_", "{": r"\{", "}": r"\}",
    "$": r"\$", "%": r"\%", "&": r"\&", "#": r"\#", "^": r"\^{}",
}


def _as_tex(name: str) -> str:
    """The name as a TeX math body, so names can be combined."""
    if _is_tex(name):
        return _strip_math_delimiters(name)
    if len(name) == 1 and name.isalpha():
        return name
    return r"\text{" + "".join(_TEXT_ESCAPES.get(ch, ch) for ch in name) + "}"


def _product_name(left, right):
    """Name for ``left @ right``: the two names side by side, like ``XW``."""
    if not left or not right:
        return None
    return f"${{{_as_tex(left)}}}{{{_as_tex(right)}}}$"


def _transpose_name(name):
    r"""Name for a transposed matrix: ``X`` becomes ``X^{\mathbf{T}}``."""
    if not name:
        return None
    return f"${{{_as_tex(name)}}}^{{\\mathbf{{T}}}}$"


def _name_parts(name: str) -> tuple[str, str]:
    """Render the name line; returns (html, plain text for the aria label)."""
    if _is_tex(name):
        # TeX: hand it to marimo's markdown, which renders math with the
        # KaTeX that ships with marimo — no extra JS or dependency.
        import marimo as mo

        tex = _strip_math_delimiters(name)
        body = mo.md(f"${tex}$").text
        plain = tex
    elif len(name) == 1 and name.isalpha():
        # A lone letter reads as a math variable and stays italic.
        body = f"<i>{escape(name)}</i>"
        plain = name
    else:
        body = escape(name)
        plain = name
    return f'<div class="ws-shape-display-name">{body}</div>', plain


def _normalize_name(name):
    if name is None:
        return None
    if not isinstance(name, str):
        raise TypeError(f"name must be a string or None, got {type(name).__name__}")
    return name.strip() or None


def _render_shape_display(array):
    import marimo as mo

    if array.ndim not in (2, 3):
        return array.value

    plain_label = " by ".join(
        str(size) if label is None else label
        for label, size in zip(array.labels, array.shape)
    )
    if array.name:
        name_div, plain_name = _name_parts(array.name)
    else:
        # Always reserve the name row so named and unnamed arrays line up
        # when they sit next to each other in an hstack.
        name_div, plain_name = '<div class="ws-shape-display-name">&nbsp;</div>', ""
    if plain_name:
        aria_label = f"Array {plain_name} with shape {plain_label}"
    else:
        aria_label = f"Array with shape {plain_label}"
    uid = uuid4().hex[:8]
    return mo.Html(
        f"""
        <style>
          .ws-shape-display {{
            --ws-shape-display-color: #374151;
            color-scheme: light dark;
            color: var(--ws-shape-display-color);
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            min-width: 96px;
            padding: 6px 8px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
              "Liberation Mono", monospace;
          }}
          .dark .ws-shape-display,
          .dark-theme .ws-shape-display,
          [data-theme="dark"] .ws-shape-display {{
            --ws-shape-display-color: #e5e7eb;
          }}
          .ws-shape-display svg {{
            display: block;
            overflow: visible;
            fill: none;
            stroke: currentColor;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
          }}
          .ws-shape-display-plane-back {{ opacity: 0.28; }}
          .ws-shape-display-plane-middle {{ opacity: 0.58; }}
          .ws-shape-display-plane-front {{ opacity: 1; }}
          .ws-shape-display-shape {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 16px;
            line-height: 1.2;
            letter-spacing: -0.01em;
            white-space: nowrap;
          }}
          .ws-shape-display-times {{ opacity: 0.65; }}
          .ws-shape-display-name {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 18px;
            line-height: 1.25;
            white-space: nowrap;
          }}
          .ws-shape-display-name sub,
          .ws-shape-display-name sup {{
            line-height: 0;
          }}
        </style>
        <div class="ws-shape-display" role="img"
             aria-label="{escape(aria_label)}">
          {name_div}
          {_planes_svg(array.ndim, uid)}
          <div class="ws-shape-display-shape">{_caption_html(array)}</div>
        </div>
        """
    )


def _carry_labels(source, shape) -> tuple:
    """Labels for an array of ``shape`` derived from ``source``.

    An axis keeps its label only if it still has the size it had in
    ``source``, so a caption is never wrong: after ``X @ W`` or a reshape the
    changed axes fall back to their live size.
    """
    labels = getattr(source, "_labels", None)
    if labels is None or len(labels) != len(shape):
        return (None,) * len(shape)
    return tuple(
        label if size == old_size else None
        for label, size, old_size in zip(labels, shape, source.shape)
    )


def _rebuild(data, labels, name):
    """Unpickle helper: restore a shape_display with its labels and name."""
    array = data.view(_shape_display_type())
    array._labels = tuple(labels)
    array._name = name
    return array


def _shape_display_type():
    """Create the ndarray subclass lazily so NumPy stays optional."""
    global _SHAPE_DISPLAY_TYPE
    if _SHAPE_DISPLAY_TYPE is not None:
        return _SHAPE_DISPLAY_TYPE

    import numpy as np

    class _ShapeDisplay(np.ndarray):
        __array_priority__ = 1000

        def __new__(cls, value, *, labels=None, name=None):
            array = np.asarray(value).view(cls)
            if array.ndim not in (2, 3):
                raise ValueError(
                    "shape_display only supports 2D and 3D arrays; "
                    f"got a {array.ndim}D array"
                )
            array._labels = _normalize_labels(labels, array.ndim)
            array._name = _normalize_name(name)
            return array

        def __array_finalize__(self, source):
            # C-level allocations (np.concatenate, np.stack, ...) call this
            # with source=None; the attribute must always exist.
            self._labels = _carry_labels(source, self.shape)
            # The name sticks to views of the same data (slices, .T,
            # reshape) and is dropped for computed results like X + 1.
            name = getattr(source, "_name", None)
            if name is not None and not np.may_share_memory(self, source):
                name = None
            self._name = name

        def __reduce_ex__(self, protocol):
            # The class is created lazily, so pickle can't find it by name;
            # rebuild through a module-level function that keeps the labels.
            return (_rebuild, (np.asarray(self), self._labels, self._name))

        @property
        def labels(self):
            """Axis labels used by the shape-only display.

            A string is rendered literally; ``None`` renders the live size of
            that axis.
            """
            return self._labels

        @labels.setter
        def labels(self, value):
            self._labels = _normalize_labels(value, self.ndim)

        @property
        def value(self):
            """The same array as a plain ``numpy.ndarray`` view."""
            return self.view(np.ndarray)

        @property
        def name(self):
            """Name shown above the glyph; a string or ``None``."""
            return self._name

        @name.setter
        def name(self, value):
            self._name = _normalize_name(value)

        def set_name(self, name):
            """Return a view of the same data with a new name.

            Handy inline, e.g. ``(X @ W).set_name("XW")``; the original array
            keeps its name. Pass ``None`` to clear it.
            """
            result = self.view(type(self))
            result._labels = self._labels
            result.name = name
            return result

        def _display_(self):
            return _render_shape_display(self)

        def transpose(self, *axes):
            result = super().transpose(*axes)
            if len(axes) == 1 and isinstance(axes[0], (tuple, list, np.ndarray)):
                # np.rot90 passes an arange; np.transpose passes tuples/lists.
                order = tuple(axes[0])
            elif not axes or (len(axes) == 1 and axes[0] is None):
                order = tuple(reversed(range(self.ndim)))
            else:
                order = tuple(axes)
            return self._permuted(result, order)

        @property
        def T(self):
            return self.transpose()

        def swapaxes(self, axis1, axis2):
            result = super().swapaxes(axis1, axis2)
            order = list(range(self.ndim))
            order[axis1], order[axis2] = order[axis2], order[axis1]
            return self._permuted(result, order)

        def _permuted(self, result, order):
            order = tuple(axis % self.ndim for axis in order)
            result._labels = tuple(self.labels[axis] for axis in order)
            if self.ndim == 2 and order == (1, 0):
                result._name = _transpose_name(self._name)
            return result

        def __matmul__(self, other):
            result = super().__matmul__(other)
            if isinstance(result, _ShapeDisplay):
                result._name = _product_name(self._name, getattr(other, "_name", None))
                if result.ndim == self.ndim and getattr(other, "ndim", 0) >= 2:
                    # Rows come from the left operand, columns from the right:
                    # (d × n) @ (n × d) is d × d.
                    other_labels = getattr(other, "_labels", None)
                    column = other_labels[-1] if other_labels else None
                    rows = _carry_labels(self, result.shape)[:-1]
                    result._labels = rows + (column,)
            return result

        def __array_function__(self, func, types, args, kwargs):
            result = super().__array_function__(func, types, args, kwargs)
            return self._with_display(result)

        def _with_display(self, result):
            if isinstance(result, np.ndarray):
                if not isinstance(result, _ShapeDisplay):
                    result = result.view(_ShapeDisplay)
                # A C-level allocation (np.concatenate, np.hstack, ...) or a
                # fresh view has no labels yet; borrow ours where sizes agree.
                # Results that already carry labels (e.g. transpose) keep them.
                if all(label is None for label in result._labels):
                    result._labels = _carry_labels(self, result.shape)
                return result
            if isinstance(result, tuple):
                return tuple(self._with_display(item) for item in result)
            if isinstance(result, list):
                return [self._with_display(item) for item in result]
            return result

    _ShapeDisplay.__name__ = "ShapeDisplay"
    _ShapeDisplay.__qualname__ = "ShapeDisplay"
    _ShapeDisplay.__module__ = __name__
    _SHAPE_DISPLAY_TYPE = _ShapeDisplay
    return _SHAPE_DISPLAY_TYPE


def shape_display(
    value: Any,
    *,
    labels: tuple[str | None, ...] | None = None,
    name: str | None = None,
):
    r"""Wrap a 2D or 3D NumPy array with a shape-only marimo display.

    The returned value is an ``numpy.ndarray`` subclass, so indexing, methods,
    arithmetic, and NumPy operations continue to work. Array-valued results
    keep the display behavior. Use ``.value`` to get a plain ``numpy.ndarray``
    view over the same data.

    ``labels`` has one entry per axis. A string is shown as a symbolic
    dimension and ``None`` is replaced by that axis's live size.

    Args:
        value: Any value accepted by ``numpy.asarray`` with two or three axes.
        labels: Optional tuple of strings and ``None`` values. Defaults
            to showing every concrete dimension.
        name: Optional title rendered above the glyph. Plain strings render
            in serif — a lone letter as an italic math variable, longer text
            upright. TeX names (containing ``\`` or wrapped in ``$...$``)
            render with marimo's built-in KaTeX. The name sticks to views
            (slices, reshapes), is inferred for ``@`` (``X @ W`` is named
            ``XW``) and 2D transposes (``X.T`` is ``X`` with a superscript
            T), and is dropped for other computed results; use
            ``.set_name(...)`` to name any result.

    Example:
        ```python
        import numpy as np
        from wigglystuff import shape_display

        X = shape_display(np.zeros((100, 2)), labels=("n", None), name=r"$\mathbf{X}$")
        X        # renders "X" over empty matrix brackets with "n × 2" underneath
        X.T      # named X with a superscript T, caption "2 × n"
        X.value  # plain ndarray view
        ```
    """
    return _shape_display_type()(value, labels=labels, name=name)


__all__ = ["shape_display"]
