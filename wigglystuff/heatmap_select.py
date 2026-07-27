"""A Bret Victor style parameter-space grid you can select cells and slices from."""

import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import anywidget
import traitlets


def _values_to_rgba(values, cmap, norm, vmin, vmax):
    """Colormap a 2D array the way matplotlib does, returning a uint8 RGBA array.

    Follows matplotlib's conventions rather than inventing new ones: ``cmap`` is
    a name or a ``Colormap``, ``norm`` is a ``Normalize`` instance, and cells
    that are masked or non-finite get the colormap's "bad" color. That last part
    is how you get a Bret-Victor-style crash region without the widget needing
    any concept of one::

        cmap = matplotlib.colormaps["gray"].with_extremes(bad="red")
        values = np.ma.masked_where(crashed, distance)

    Args:
        values: 2D numeric array, optionally a masked array.
        cmap: Colormap name or ``matplotlib.colors.Colormap`` instance.
        norm: Optional ``Normalize`` instance, e.g. ``LogNorm()``. Mutually
            exclusive with ``vmin``/``vmax``.
        vmin: Optional lower end of the color scale.
        vmax: Optional upper end of the color scale.

    Returns:
        np.ndarray: ``(rows, cols, 4)`` uint8 RGBA.
    """
    import matplotlib
    import numpy as np
    from matplotlib import colors as mcolors

    if norm is not None and (vmin is not None or vmax is not None):
        raise ValueError("pass either norm or vmin/vmax, not both")

    colormap = matplotlib.colormaps[cmap] if isinstance(cmap, str) else cmap

    if norm is None:
        # Autoscale off the finite values only, so a NaN doesn't poison the
        # range and turn the whole grid into the "bad" color.
        if vmin is None or vmax is None:
            finite = np.asarray(values)[np.isfinite(values)]
            if vmin is None:
                vmin = float(finite.min()) if finite.size else 0.0
            if vmax is None:
                vmax = float(finite.max()) if finite.size else 1.0
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    return colormap(norm(values), bytes=True)


def _image_to_png_base64(
    image, cmap="gray", norm=None, vmin=None, vmax=None
) -> Tuple[str, int, int]:
    """Turn anything image-like into a data URI plus its pixel dimensions.

    One image pixel is one grid cell, so the returned dimensions double as the
    grid shape. Accepted inputs, in the order they are sniffed:

    - a ``data:`` URI or a bare base64 PNG string (needs nothing)
    - a filesystem path to an image (needs nothing)
    - a PIL ``Image`` (needs pillow, which you already have if you have one)
    - a ``(rows, cols, 3|4)`` uint8 array (needs pillow)
    - a ``(rows, cols)`` numeric array, colormapped by ``_values_to_rgba``

    Args:
        image: The image-like object described above.
        cmap: Colormap name or instance, for 2D numeric arrays.
        norm: Optional ``Normalize`` instance, for 2D numeric arrays.
        vmin: Optional lower end of the color scale.
        vmax: Optional upper end of the color scale.

    Returns:
        tuple: ``(data_uri, n_rows, n_cols)``.
    """
    if isinstance(image, Path):
        image = str(image)

    if isinstance(image, str):
        # A path on disk, or an already-encoded PNG.
        if image.startswith("data:"):
            payload = image.split(",", 1)[1]
            return image, *_png_dimensions(base64.b64decode(payload))
        looks_like_base64 = "\n" not in image and len(image) > 256
        if not looks_like_base64:
            raw = Path(image).read_bytes()
            encoded = base64.b64encode(raw).decode()
            return f"data:image/png;base64,{encoded}", *_png_dimensions(raw)
        raw = base64.b64decode(image)
        return f"data:image/png;base64,{image}", *_png_dimensions(raw)

    if hasattr(image, "save"):  # a PIL Image
        return _pil_to_data_uri(image)

    if hasattr(image, "shape"):
        import numpy as np

        # np.asarray would drop the mask, and masked cells are how you get a
        # "bad" color, so leave masked arrays alone.
        arr = image if isinstance(image, np.ma.MaskedArray) else np.asarray(image)
        if arr.ndim == 2:
            arr = _values_to_rgba(arr, cmap, norm, vmin, vmax)
        elif arr.ndim != 3 or arr.shape[2] not in (3, 4):
            raise ValueError(
                "image arrays must be 2D, or 3D with 3 or 4 channels, "
                f"got shape {arr.shape}"
            )

        if arr.dtype != np.uint8:
            arr = np.clip(arr, 0, 255).astype(np.uint8)

        from PIL import Image

        return _pil_to_data_uri(Image.fromarray(arr))

    raise TypeError(
        "image must be a base64/data-URI string, a path, a PIL Image, or an array, "
        f"got {type(image).__name__}"
    )


def _pil_to_data_uri(pil_image) -> Tuple[str, int, int]:
    """Encode a PIL image as a PNG data URI plus its ``(rows, cols)``."""
    buf = BytesIO()
    pil_image.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    width, height = pil_image.size
    return f"data:image/png;base64,{encoded}", height, width


def _png_dimensions(raw: bytes) -> Tuple[int, int]:
    """Read ``(rows, cols)`` straight out of a PNG's IHDR chunk.

    Avoids needing pillow just to learn the grid shape of a pre-encoded image.
    """
    if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("image bytes are not a PNG")
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    return height, width


class HeatmapSelect(anywidget.AnyWidget):
    """A dense parameter-space grid where you pick one cell or a whole row/column.

    Modelled on the grid in Bret Victor's *Up and Down the Ladder of
    Abstraction*. The body picks a single cell; the left gutter picks a whole row
    (a horizontal band); the bottom gutter picks a whole column (a vertical band).

    Hovering previews, clicking *pins*. The three pins are independent and
    coexist — you can hold a cell, a row and a column at once, and clicking one
    region only replaces that region's pin. Double-clicking a region drops just
    that pin. What to make of a combination is the caller's business.

    One pixel of ``image`` is one grid cell, and the values behind the picture
    never cross the wire — the widget hands back indices, and you do the slicing
    yourself with ``values[widget.pinned_row]``. Use ``x_at``/``y_at`` to turn an
    index back into a data coordinate.

    Examples:
        ```python
        import numpy as np
        import marimo as mo
        from wigglystuff import HeatmapSelect

        steps = np.random.rand(100, 91)
        widget = mo.ui.anywidget(
            HeatmapSelect(
                steps,
                x_range=(0, 90),
                y_range=(0.1, 10.0),
                x_label="bend angle",
                y_label="turning rate",
                x_suffix="°",
                y_suffix="°",
            )
        )
        widget
        ```

        Then react to the pins in another cell. They are independent, so this is
        three ``if``s rather than a branch:

        ```python
        if widget.pinned_row is not None:
            row_sweep = steps[widget.pinned_row, :]
        if widget.pinned_col is not None:
            col_sweep = steps[:, widget.pinned_col]
        if widget.pinned_cell is not None:
            row, col = widget.pinned_cell
            value = steps[row, col]
            x, y = widget.x_at(col), widget.y_at(row)
        ```

        Coloring follows matplotlib, so a Bret-Victor-style crash region is just
        a masked array plus a "bad" color — the widget has no concept of one:

        ```python
        import matplotlib

        HeatmapSelect(
            np.ma.masked_where(crashed, distance),
            cmap=matplotlib.colormaps["gray"].with_extremes(bad="red"),
        )
        ```
    """

    _esm = Path(__file__).parent / "static" / "heatmap-select.js"
    _css = Path(__file__).parent / "static" / "heatmap-select.css"

    image_base64 = traitlets.Unicode("").tag(sync=True)
    n_rows = traitlets.Int(1).tag(sync=True)
    n_cols = traitlets.Int(1).tag(sync=True)
    x_range = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)
    y_range = traitlets.Tuple(
        traitlets.Float(), traitlets.Float(), default_value=(0.0, 1.0)
    ).tag(sync=True)
    x_label = traitlets.Unicode("").tag(sync=True)
    y_label = traitlets.Unicode("").tag(sync=True)
    x_suffix = traitlets.Unicode("").tag(sync=True)
    y_suffix = traitlets.Unicode("").tag(sync=True)
    origin = traitlets.Unicode("lower").tag(sync=True)
    cell_width = traitlets.Int(4).tag(sync=True)
    cell_height = traitlets.Int(4).tag(sync=True)

    # Row and column bands are tinted differently so the two axes are
    # distinguishable at a glance. Set these to the same colors your downstream
    # chart uses and the two line up. Empty falls back to the CSS variables.
    row_color = traitlets.Unicode("").tag(sync=True)
    col_color = traitlets.Unicode("").tag(sync=True)

    # Three pins that coexist: one cell, one row grabbed from the left axis, one
    # column grabbed from the bottom axis. Clicking a region replaces only that
    # region's pin. ``None`` means nothing is pinned there.
    pinned_cell = traitlets.Tuple(
        traitlets.Int(), traitlets.Int(), allow_none=True, default_value=None
    ).tag(sync=True)
    pinned_row = traitlets.Int(allow_none=True, default_value=None).tag(sync=True)
    pinned_col = traitlets.Int(allow_none=True, default_value=None).tag(sync=True)

    # The same three shapes for whatever the cursor is over right now. Only one
    # is ever set at a time, since the cursor is only ever in one region.
    hover_cell = traitlets.Tuple(
        traitlets.Int(), traitlets.Int(), allow_none=True, default_value=None
    ).tag(sync=True)
    hover_row = traitlets.Int(allow_none=True, default_value=None).tag(sync=True)
    hover_col = traitlets.Int(allow_none=True, default_value=None).tag(sync=True)

    # Hover fires on every mouse move, so this defaults to coalescing rather than
    # to ChartPuck's 0 — a bare mousemove flood is a round trip per pixel.
    throttle = traitlets.Union(
        [traitlets.Int(), traitlets.Unicode()], default_value=50
    ).tag(sync=True)

    def __init__(
        self,
        image: Any,
        *,
        x_range: Tuple[float, float] = (0.0, 1.0),
        y_range: Tuple[float, float] = (0.0, 1.0),
        x_label: str = "",
        y_label: str = "",
        x_suffix: str = "",
        y_suffix: str = "",
        origin: str = "lower",
        cell_width: int = 4,
        cell_height: int = 4,
        row_color: str = "",
        col_color: str = "",
        cmap: Any = "gray",
        norm: Any = None,
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        throttle: Union[int, str] = 50,
        **kwargs: Any,
    ):
        """Create a HeatmapSelect widget.

        Args:
            image: The grid bitmap — one pixel per cell. Accepts a base64/data-URI
                PNG string, a path, a PIL ``Image``, an ``(rows, cols, 3|4)`` uint8
                array, or a ``(rows, cols)`` numeric array colormapped via
                ``cmap``/``norm``/``vmin``/``vmax``.
            x_range: Data coordinates of the first and last *column* centers.
            y_range: Data coordinates of the first and last *row* centers.
            x_label: Label drawn under the bottom gutter.
            y_label: Label drawn beside the left gutter.
            x_suffix: Suffix appended to x tick labels, e.g. ``"°"``.
            y_suffix: Suffix appended to y tick labels.
            origin: ``"lower"`` puts image row 0 at ``y_range[0]`` (bottom),
                ``"upper"`` puts it at the top, matching matplotlib's ``imshow``.
            cell_width: Screen pixels per cell horizontally.
            cell_height: Screen pixels per cell vertically.
            row_color: Tint for the row band grabbed from the left (y) axis, e.g.
                ``"#1f4fd8"``. Empty uses the ``--hs-row-color`` CSS variable.
            col_color: Tint for the column band grabbed from the bottom (x) axis.
                Empty uses the ``--hs-col-color`` CSS variable.
            cmap: Colormap name or ``matplotlib.colors.Colormap``, for 2D numeric
                arrays. Grayscale by default. Mask cells (or make them NaN) and
                use ``cmap.with_extremes(bad="red")`` to color a crash region.
            norm: Optional ``matplotlib.colors.Normalize`` instance, e.g.
                ``LogNorm()``. Mutually exclusive with ``vmin``/``vmax``.
            vmin: Optional lower end of the color scale.
            vmax: Optional upper end of the color scale.
            throttle: How often hover updates reach Python — ``0`` for every
                mouse move, an int for milliseconds, or ``"dragend"`` to send
                hover only on release. Pin changes always sync immediately,
                whatever this is set to.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if origin not in ("lower", "upper"):
            raise ValueError(f"origin must be 'lower' or 'upper', got {origin!r}")
        if cell_width < 1 or cell_height < 1:
            raise ValueError("cell_width and cell_height must be at least 1")
        for name, value in (("x_range", x_range), ("y_range", y_range)):
            if len(tuple(value)) != 2:
                raise ValueError(f"{name} must be a (min, max) pair, got {value!r}")

        # Remembered so set_image() recolors the same way without repeating them.
        self._color_kwargs = {"cmap": cmap, "norm": norm, "vmin": vmin, "vmax": vmax}
        image_base64, n_rows, n_cols = _image_to_png_base64(
            image, **self._color_kwargs
        )

        super().__init__(
            image_base64=image_base64,
            n_rows=n_rows,
            n_cols=n_cols,
            x_range=tuple(float(v) for v in x_range),
            y_range=tuple(float(v) for v in y_range),
            x_label=x_label,
            y_label=y_label,
            x_suffix=x_suffix,
            y_suffix=y_suffix,
            origin=origin,
            cell_width=cell_width,
            cell_height=cell_height,
            row_color=row_color,
            col_color=col_color,
            throttle=throttle,
            **kwargs,
        )

    @property
    def width(self) -> int:
        """Width of the grid area in screen pixels (excludes the gutters)."""
        return self.n_cols * self.cell_width

    @property
    def height(self) -> int:
        """Height of the grid area in screen pixels (excludes the gutters)."""
        return self.n_rows * self.cell_height

    def x_at(self, col: Optional[int]) -> Optional[float]:
        """Data coordinate at the center of a column, or ``None`` for ``None``.

        Args:
            col: Column index, or ``None``.

        Returns:
            float | None: The x coordinate, interpolated across ``x_range``.
        """
        if col is None:
            return None
        lo, hi = self.x_range
        if self.n_cols <= 1:
            return lo
        return lo + (col / (self.n_cols - 1)) * (hi - lo)

    def y_at(self, row: Optional[int]) -> Optional[float]:
        """Data coordinate at the center of a row, or ``None`` for ``None``.

        Args:
            row: Row index, or ``None``.

        Returns:
            float | None: The y coordinate, interpolated across ``y_range``.
        """
        if row is None:
            return None
        lo, hi = self.y_range
        if self.n_rows <= 1:
            return lo
        return lo + (row / (self.n_rows - 1)) * (hi - lo)

    @property
    def selection(self) -> dict:
        """All six selection traits in one dict, handy for one-shot reads."""
        return {
            "pinned_cell": self.pinned_cell,
            "pinned_row": self.pinned_row,
            "pinned_col": self.pinned_col,
            "hover_cell": self.hover_cell,
            "hover_row": self.hover_row,
            "hover_col": self.hover_col,
        }

    def clear(self) -> None:
        """Drop all three pins and the current hover."""
        with self.hold_sync():
            self.pinned_cell = None
            self.pinned_row = None
            self.pinned_col = None
            self.hover_cell = None
            self.hover_row = None
            self.hover_col = None

    def set_image(self, image: Any, **color_kwargs: Any) -> None:
        """Swap the grid bitmap, re-deriving the grid shape from its pixels.

        Args:
            image: A new image, in any of the forms the constructor accepts.
            **color_kwargs: Optional ``cmap``/``norm``/``vmin``/``vmax`` overrides;
                anything omitted reuses what the constructor was given.
        """
        self._color_kwargs.update(color_kwargs)
        image_base64, n_rows, n_cols = _image_to_png_base64(
            image, **self._color_kwargs
        )
        with self.hold_sync():
            self.image_base64 = image_base64
            self.n_rows = n_rows
            self.n_cols = n_cols
