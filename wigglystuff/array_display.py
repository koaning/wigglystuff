"""Shape-only displays for NumPy arrays in marimo notebooks."""

from __future__ import annotations

import re
from html import escape
from typing import Any
from uuid import uuid4


_ARRAY_DISPLAY_TYPE = None


def _normalize_display_shape(display_shape, ndim):
    if display_shape is None:
        return (None,) * ndim

    display_shape = tuple(display_shape)
    if len(display_shape) != ndim:
        raise ValueError(
            "display_shape must have one entry per array axis; "
            f"got {len(display_shape)} entries for a {ndim}D array"
        )
    if any(part is not None and not isinstance(part, str) for part in display_shape):
        raise TypeError("display_shape entries must be strings or None")
    if any(part == "" for part in display_shape):
        raise ValueError("display_shape labels cannot be empty")
    return display_shape


def _display_shape_html(array) -> str:
    parts = []
    for label, size in zip(array.display_shape, array.shape):
        if label is None:
            parts.append(f'<span class="ws-array-display-size">{size}</span>')
        else:
            parts.append(f"<var>{escape(label)}</var>")
    return '<span class="ws-array-display-times"> × </span>'.join(parts)


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
        <mask id="ws-array-display-back-{uid}" maskUnits="userSpaceOnUse"
              x="0" y="0" width="96" height="76">
          <rect x="0" y="0" width="96" height="76" fill="white" />
          <rect x="19.75" y="10.75" width="50.5" height="54.5" fill="black" />
          <rect x="12.75" y="17.75" width="50.5" height="54.5" fill="black" />
        </mask>
        <mask id="ws-array-display-middle-{uid}" maskUnits="userSpaceOnUse"
              x="0" y="0" width="96" height="76">
          <rect x="0" y="0" width="96" height="76" fill="white" />
          <rect x="12.75" y="17.75" width="50.5" height="54.5" fill="black" />
        </mask>
      </defs>
      <g class="ws-array-display-plane ws-array-display-plane-back"
         mask="url(#ws-array-display-back-{uid})">
        <path d="M39 5H28v52h11 M65 5h11v52H65" />
      </g>
      <g class="ws-array-display-plane ws-array-display-plane-middle"
         mask="url(#ws-array-display-middle-{uid})">
        <path d="M32 12H21v52h11 M58 12h11v52H58" />
      </g>
      <g class="ws-array-display-plane ws-array-display-plane-front">
        <path d="M25 19H14v52h11 M51 19h11v52H51" />
      </g>
    </svg>
    """


# ---------------------------------------------------------------------------
# Names: plain text, or a small LaTeX subset rendered via Unicode so no
# renderer, JavaScript, or extra dependency is needed.

_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
    "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π",
    "rho": "ρ", "sigma": "σ", "varsigma": "ς", "tau": "τ",
    "upsilon": "υ", "phi": "φ", "varphi": "ϕ", "chi": "χ", "psi": "ψ",
    "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ",
    "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}

_BOLD_GREEK_LOWER = "αβγδεζηθικλμνξοπρστυφχψω"
_BOLD_GREEK_CAPITAL = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"

_DOUBLE_STRUCK = {
    "C": "ℂ", "E": "𝔼", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ",
    "R": "ℝ", "Z": "ℤ",
}

# The Unicode script block skips these letters; use the letterlike lookalikes.
_SCRIPT_HOLES = {
    "B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ", "L": "ℒ",
    "M": "ℳ", "R": "ℛ",
}

_ACCENTS = {
    "hat": "\u0302", "tilde": "\u0303", "bar": "\u0304", "vec": "\u20d7",
    "dot": "\u0307", "ddot": "\u0308",
}

_SYMBOLS = {
    "times": "×", "cdot": "⋅", "top": "⊤", "perp": "⊥", "infty": "∞",
    "in": "∈", "notin": "∉", "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥",
    "neq": "≠", "ne": "≠", "approx": "≈", "equiv": "≡", "sim": "∼",
    "propto": "∝", "pm": "±", "mp": "∓", "partial": "∂", "nabla": "∇",
    "ell": "ℓ", "hbar": "ℏ", "langle": "⟨", "rangle": "⟩", "sum": "∑",
    "prod": "∏", "int": "∫", "cup": "∪", "cap": "∩", "subseteq": "⊆",
    "setminus": "∖", "left": "", "right": "",
    # Spacing and control symbols.
    "quad": "\u2002", "qquad": "\u2003", "\\": "\u2002", ",": "\u2009",
    ";": "\u2005", ":": "\u2005", " ": "\u2009", "!": "",
}

_UPRIGHT_COMMANDS = ("mathrm", "text", "operatorname", "mbox", "mathsf", "mathtt")
_BOLD_COMMANDS = ("mathbf", "bm", "boldsymbol")


def _bold_char(char: str) -> str:
    if "A" <= char <= "Z":
        return chr(0x1D400 + ord(char) - ord("A"))
    if "a" <= char <= "z":
        return chr(0x1D41A + ord(char) - ord("a"))
    index = _BOLD_GREEK_LOWER.find(char)
    if index >= 0:
        return chr(0x1D6E2 + index)
    index = _BOLD_GREEK_CAPITAL.find(char)
    if index >= 0:
        return chr(0x1D6A8 + index)
    return char


def _script_char(char: str) -> str:
    if "A" <= char <= "Z":
        return _SCRIPT_HOLES.get(char) or chr(0x1D49C + ord(char) - ord("A"))
    return char


def _styled_char(char: str, style):
    if style == "bold":
        return _bold_char(char)
    if style == "script":
        return _script_char(char)
    if style == "double":
        return _DOUBLE_STRUCK.get(char, char)
    if style is None and char.isalpha():
        return f"<i>{char}</i>"
    return char


def _read_command(tex: str, i: int, end: int):
    """Read the command name starting at ``tex[i] == "\\"``."""
    j = i + 1
    while j < end and tex[j].isalpha():
        j += 1
    if j > i + 1:
        return tex[i + 1:j], j
    if j < end:  # control symbol such as \\ or \,
        return tex[j], j + 1
    return "", end


def _read_group(tex: str, i: int, end: int):
    """Read a ``{...}`` group (or a single token) starting at ``i``."""
    while i < end and tex[i].isspace():
        i += 1
    if i >= end:
        return "", i
    if tex[i] == "{":
        depth = 0
        for j in range(i, end):
            if tex[j] == "{":
                depth += 1
            elif tex[j] == "}":
                depth -= 1
                if depth == 0:
                    return tex[i + 1:j], j + 1
        return tex[i + 1:end], end
    if tex[i] == "\\":
        _, j = _read_command(tex, i, end)
        return tex[i:j], j
    return tex[i], i + 1


def _attach_accent(token: str, mark: str) -> str:
    if token.endswith("</i>"):
        return token[:-4] + mark + "</i>"
    return token + mark


def _convert_next(tex: str, i: int, end: int, style):
    """Convert the single token after ``i`` (group, command, or character)."""
    while i < end and tex[i].isspace():
        i += 1
    if i >= end:
        return "", i
    if tex[i] == "{":
        body, j = _read_group(tex, i, end)
        return _convert(body, 0, len(body), style)[0], j
    if tex[i] == "\\":
        name, j = _read_command(tex, i, end)
        if name in _ACCENTS:
            token, j = _convert_next(tex, j, end, style)
            return _attach_accent(token, _ACCENTS[name]), j
        html, _ = _convert(tex[i:j], 0, j - i, style)
        return html, j
    return _styled_char(escape(tex[i]), style), i + 1


def _convert(tex: str, i: int, end: int, style):
    """Convert ``tex[i:end]`` to HTML; ``style`` restyles plain characters."""
    out = []
    while i < end:
        ch = tex[i]
        if ch == "\\":
            name, i = _read_command(tex, i, end)
            if name in _GREEK:
                char = _GREEK[name]
                if style == "bold":
                    out.append(_bold_char(char))
                elif style is None and char.islower():
                    out.append(f"<i>{char}</i>")
                else:
                    out.append(char)
            elif name in _SYMBOLS:
                out.append(_SYMBOLS[name])
            elif name in _ACCENTS:
                token, i = _convert_next(tex, i, end, style)
                out.append(_attach_accent(token, _ACCENTS[name]))
            elif name in _UPRIGHT_COMMANDS:
                body, i = _read_group(tex, i, end)
                out.append(_convert(body, 0, len(body), "upright")[0])
            elif name in _BOLD_COMMANDS:
                body, i = _read_group(tex, i, end)
                out.append(_convert(body, 0, len(body), "bold")[0])
            elif name in ("mathcal", "mathscr"):
                body, i = _read_group(tex, i, end)
                out.append(_convert(body, 0, len(body), "script")[0])
            elif name == "mathbb":
                body, i = _read_group(tex, i, end)
                out.append(_convert(body, 0, len(body), "double")[0])
            elif name == "mathit":
                body, i = _read_group(tex, i, end)
                out.append(_convert(body, 0, len(body), None)[0])
            elif name:
                out.append(escape("\\" + name))  # degrade to readable text
        elif ch in "_^":
            token, i = _convert_next(tex, i + 1, end, style)
            tag = "sub" if ch == "_" else "sup"
            out.append(f"<{tag}>{token}</{tag}>")
        elif ch == "{":
            body, i = _read_group(tex, i, end)
            out.append(_convert(body, 0, len(body), style)[0])
        elif ch == "}":
            i += 1  # stray closing brace
        elif ch.isspace():
            if style == "upright":
                out.append(" ")
            i += 1
        else:
            out.append(_styled_char(escape(ch), style))
            i += 1
    return "".join(out), i


def _looks_like_latex(name: str) -> bool:
    return "\\" in name or name.startswith("$")


def _tex_to_html(name: str) -> str:
    tex = name.strip()
    for left, right in (("$$", "$$"), ("$", "$"), (r"\(", r"\)"), (r"\[", r"\]")):
        if len(tex) >= 2 * len(left) and tex.startswith(left) and tex.endswith(right):
            tex = tex[len(left):len(tex) - len(right)].strip()
            break
    return _convert(tex, 0, len(tex), None)[0]


def _name_parts(name: str) -> tuple[str, str]:
    """Render the name line; returns (html, plain text for the aria label)."""
    if _looks_like_latex(name):
        body = _tex_to_html(name)
        plain = re.sub(r"<[^>]+>", "", body)
    else:
        # A lone letter reads as a math variable and stays italic; anything
        # longer is normal text and stays upright.
        if len(name) == 1 and name.isalpha():
            body = f"<i>{escape(name)}</i>"
        else:
            body = escape(name)
        plain = name
    return f'<div class="ws-array-display-name">{body}</div>', plain


def _normalize_name(name):
    if name is None:
        return None
    if not isinstance(name, str):
        raise TypeError(f"name must be a string or None, got {type(name).__name__}")
    return name.strip() or None


def _render_array_display(array):
    import marimo as mo

    if array.ndim not in (2, 3):
        return array.value

    plain_label = " by ".join(
        str(size) if label is None else label
        for label, size in zip(array.display_shape, array.shape)
    )
    name_div, plain_name = _name_parts(array.name) if array.name else ("", "")
    if plain_name:
        aria_label = f"Array {plain_name} with shape {plain_label}"
    else:
        aria_label = f"Array with shape {plain_label}"
    uid = uuid4().hex[:8]
    return mo.Html(
        f"""
        <style>
          .ws-array-display {{
            --ws-array-display-color: #374151;
            color-scheme: light dark;
            color: var(--ws-array-display-color);
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
          .dark .ws-array-display,
          .dark-theme .ws-array-display,
          [data-theme="dark"] .ws-array-display {{
            --ws-array-display-color: #e5e7eb;
          }}
          .ws-array-display svg {{
            display: block;
            overflow: visible;
            fill: none;
            stroke: currentColor;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
          }}
          .ws-array-display-plane-back {{ opacity: 0.28; }}
          .ws-array-display-plane-middle {{ opacity: 0.58; }}
          .ws-array-display-plane-front {{ opacity: 1; }}
          .ws-array-display-shape {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 16px;
            line-height: 1.2;
            letter-spacing: -0.01em;
            white-space: nowrap;
          }}
          .ws-array-display-times {{ opacity: 0.65; }}
          .ws-array-display-name {{
            font-family: Georgia, "Times New Roman", serif;
            font-size: 18px;
            line-height: 1.25;
            white-space: nowrap;
          }}
          .ws-array-display-name sub,
          .ws-array-display-name sup {{
            line-height: 0;
          }}
        </style>
        <div class="ws-array-display" role="img"
             aria-label="{escape(aria_label)}">
          {name_div}
          {_planes_svg(array.ndim, uid)}
          <div class="ws-array-display-shape">{_display_shape_html(array)}</div>
        </div>
        """
    )


def _array_display_type():
    """Create the ndarray subclass lazily so NumPy stays optional."""
    global _ARRAY_DISPLAY_TYPE
    if _ARRAY_DISPLAY_TYPE is not None:
        return _ARRAY_DISPLAY_TYPE

    import numpy as np

    class _ArrayDisplay(np.ndarray):
        __array_priority__ = 1000

        def __new__(cls, value, *, display_shape=None, name=None):
            array = np.asarray(value).view(cls)
            if array.ndim not in (2, 3):
                raise ValueError(
                    "array_display only supports 2D and 3D arrays; "
                    f"got a {array.ndim}D array"
                )
            array._display_shape = _normalize_display_shape(display_shape, array.ndim)
            array._name = _normalize_name(name)
            return array

        def __array_finalize__(self, source):
            inherited = getattr(source, "_display_shape", None)
            if inherited is not None and len(inherited) == self.ndim:
                self._display_shape = inherited
            else:
                # C-level allocations (np.concatenate, np.stack, ...) call
                # this with source=None; make sure the attribute always exists.
                self._display_shape = (None,) * self.ndim
            # The name follows the data: views and elementwise results keep
            # it, while arrays rebuilt from several inputs drop it.
            self._name = getattr(source, "_name", None)

        @property
        def display_shape(self):
            """Axis labels used by the shape-only display.

            A string is rendered literally; ``None`` renders the live size of
            that axis.
            """
            return self._display_shape

        @display_shape.setter
        def display_shape(self, value):
            self._display_shape = _normalize_display_shape(value, self.ndim)

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

        def _display_(self):
            return _render_array_display(self)

        def transpose(self, *axes):
            result = super().transpose(*axes)
            if len(axes) == 1 and isinstance(axes[0], (tuple, list, np.ndarray)):
                # np.rot90 passes an arange; np.transpose passes tuples/lists.
                order = tuple(axes[0])
            elif not axes or (len(axes) == 1 and axes[0] is None):
                order = tuple(reversed(range(self.ndim)))
            else:
                order = tuple(axes)
            result._display_shape = tuple(self.display_shape[axis] for axis in order)
            return result

        @property
        def T(self):
            return self.transpose()

        def swapaxes(self, axis1, axis2):
            result = super().swapaxes(axis1, axis2)
            order = list(range(self.ndim))
            order[axis1], order[axis2] = order[axis2], order[axis1]
            result._display_shape = tuple(self.display_shape[axis] for axis in order)
            return result

        def __array_function__(self, func, types, args, kwargs):
            result = super().__array_function__(func, types, args, kwargs)
            return self._with_display(result)

        def _with_display(self, result):
            if isinstance(result, np.ndarray):
                if not isinstance(result, _ArrayDisplay):
                    result = result.view(_ArrayDisplay)
                # Carry the labels over when the result has the same number
                # of axes but only default ones — either we just created the
                # view, or a C-level allocation (np.concatenate, np.hstack,
                # ...) produced it without labels. Results that already carry
                # labels (e.g. from transpose) keep them.
                if result.ndim == self.ndim and all(
                    label is None for label in result._display_shape
                ):
                    result._display_shape = self.display_shape
                return result
            if isinstance(result, tuple):
                return tuple(self._with_display(item) for item in result)
            if isinstance(result, list):
                return [self._with_display(item) for item in result]
            return result

    _ArrayDisplay.__name__ = "ArrayDisplay"
    _ArrayDisplay.__qualname__ = "ArrayDisplay"
    _ArrayDisplay.__module__ = __name__
    _ARRAY_DISPLAY_TYPE = _ArrayDisplay
    return _ARRAY_DISPLAY_TYPE


def array_display(
    value: Any,
    *,
    display_shape: tuple[str | None, ...] | None = None,
    name: str | None = None,
):
    r"""Wrap a 2D or 3D NumPy array with a shape-only marimo display.

    The returned value is an ``numpy.ndarray`` subclass, so indexing, methods,
    arithmetic, and NumPy operations continue to work. Array-valued results
    keep the display behavior. Use ``.value`` to get a plain ``numpy.ndarray``
    view over the same data.

    ``display_shape`` has one entry per axis. A string is shown as a symbolic
    dimension and ``None`` is replaced by that axis's live size.

    Args:
        value: Any value accepted by ``numpy.asarray`` with two or three axes.
        display_shape: Optional tuple of strings and ``None`` values. Defaults
            to showing every concrete dimension.
        name: Optional label rendered above the glyph. Plain strings render in
            serif — a lone letter as an italic math variable, longer text
            upright; TeX-flavored names (containing ``\`` or wrapped in
            ``$...$``) render through a small LaTeX subset — bold
            (``\mathbf``), Greek, accents (``\hat``), sub/superscripts,
            ``\mathbb``, ``\mathcal`` — using Unicode, so no renderer or
            extra dependency is needed. The name follows the data: views and
            elementwise results keep it, arrays rebuilt from several inputs
            drop it.

    Example:
        ```python
        import numpy as np
        from wigglystuff import array_display

        X = array_display(np.zeros((100, 2)), display_shape=("n", None), name=r"$\mathbf{X}$")
        X + 1  # renders "X" over empty matrix brackets with "n × 2" underneath
        X.value  # plain ndarray view
        ```
    """
    return _array_display_type()(value, display_shape=display_shape, name=name)


__all__ = ["array_display"]
