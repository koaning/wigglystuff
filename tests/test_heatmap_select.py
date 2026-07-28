"""Tests for HeatmapSelect widget."""

import base64
import io

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image")

from wigglystuff.heatmap_select import HeatmapSelect, _png_dimensions


@pytest.fixture
def values():
    """A deterministic 20x30 field, so rows != cols catches transposition."""
    rng = np.random.default_rng(0)
    return rng.random((20, 30))


def decode(widget):
    """Decode the widget's synced bitmap back into an RGB array."""
    payload = widget.image_base64.split(",", 1)[1]
    image = Image.open(io.BytesIO(base64.b64decode(payload)))
    return np.array(image.convert("RGB"))


def test_heatmap_select_importable():
    from wigglystuff import HeatmapSelect  # noqa: F401


def test_accepts_every_image_form(values, tmp_path):
    """One image pixel is one cell, so every input form must give (20, 30)."""
    png = tmp_path / "grid.png"
    Image.new("RGB", (30, 20), "blue").save(png)

    forms = [
        values,  # 2D numeric, colormapped
        (np.random.default_rng(1).random((20, 30, 3)) * 255).astype(np.uint8),
        HeatmapSelect(values).image_base64,  # a data URI round-tripping back in
        Image.new("RGB", (30, 20), "red"),
        png,
        np.ma.masked_where(values > 0.9, values),
    ]
    for form in forms:
        widget = HeatmapSelect(form)
        assert (widget.n_rows, widget.n_cols) == (20, 30)


def test_derived_pixel_size(values):
    widget = HeatmapSelect(values, cell_width=4, cell_height=3)
    assert (widget.width, widget.height) == (30 * 4, 20 * 3)


def test_masked_cells_get_the_colormap_bad_color(values):
    """Masking plus a "bad" color is how you get a crash region, matplotlib-style."""
    matplotlib = pytest.importorskip("matplotlib")
    crashed = values > 0.8
    cmap = matplotlib.colormaps["gray"].with_extremes(bad="red")
    pixels = decode(HeatmapSelect(np.ma.masked_where(crashed, values), cmap=cmap))

    assert (pixels[crashed] == [255, 0, 0]).all()
    # Everything else stays grey, i.e. R == G == B.
    kept = pixels[~crashed]
    assert (kept[:, 0] == kept[:, 1]).all() and (kept[:, 1] == kept[:, 2]).all()


def test_nan_does_not_poison_the_color_scale(values):
    """A bare NaN must not drag vmin/vmax to NaN and blank the whole grid."""
    matplotlib = pytest.importorskip("matplotlib")
    holed = values.copy()
    holed[0, 0] = np.nan
    cmap = matplotlib.colormaps["gray"].with_extremes(bad="red")
    pixels = decode(HeatmapSelect(holed, cmap=cmap))

    assert (pixels[0, 0] == [255, 0, 0]).all()
    assert len(np.unique(pixels[1:, :, 0])) > 50, "rest of the grid lost its gradient"


def test_norm_and_vmin_vmax_are_mutually_exclusive(values):
    colors = pytest.importorskip("matplotlib.colors")
    with pytest.raises(ValueError, match="either norm or vmin/vmax"):
        HeatmapSelect(values, norm=colors.LogNorm(), vmin=0.0)


def test_rejects_bad_arguments(values):
    """Constructor validation, grouped so one test covers the whole surface."""
    cases = [
        ({"origin": "sideways"}, "origin must be"),
        ({"cell_width": 0}, "at least 1"),
        ({"cell_height": 0}, "at least 1"),
        ({"x_range": (0.0, 1.0, 2.0)}, "must be a .min, max. pair"),
    ]
    for kwargs, message in cases:
        with pytest.raises(ValueError, match=message):
            HeatmapSelect(values, **kwargs)

    with pytest.raises(ValueError, match="must be 2D, or 3D"):
        HeatmapSelect(np.zeros((4, 4, 5)))
    with pytest.raises(TypeError, match="image must be"):
        HeatmapSelect(object())


def test_three_pins_are_independent(values):
    """The whole point: a cell, a row and a column coexist."""
    widget = HeatmapSelect(values)
    assert widget.selection == {
        "pinned_cell": None,
        "pinned_row": None,
        "pinned_col": None,
        "hover_cell": None,
        "hover_row": None,
        "hover_col": None,
    }

    widget.pinned_cell = (5, 6)
    widget.pinned_row = 11
    widget.pinned_col = 12
    assert (widget.pinned_cell, widget.pinned_row, widget.pinned_col) == (
        (5, 6),
        11,
        12,
    )

    widget.clear()
    assert widget.selection == dict.fromkeys(widget.selection, None)


def test_pinned_cell_accepts_a_list(values):
    """The frontend sends JSON arrays, which must land as tuples."""
    widget = HeatmapSelect(values)
    widget.pinned_cell = [3, 4]
    assert widget.pinned_cell == (3, 4)


def test_coordinate_helpers(values):
    widget = HeatmapSelect(values, x_range=(0.0, 90.0), y_range=(5.0, 60.0))
    # x_range/y_range name the FIRST and LAST cell centers.
    assert widget.x_at(0) == 0.0
    assert widget.x_at(29) == 90.0
    assert widget.y_at(0) == 5.0
    assert widget.y_at(19) == 60.0
    assert widget.x_at(None) is None and widget.y_at(None) is None


def test_set_image_preserves_the_pins(values):
    """Recoloring on a slider change must not throw the selection away."""
    widget = HeatmapSelect(values)
    widget.pinned_cell = (1, 2)
    widget.pinned_row = 9
    before = widget.image_base64

    # A different *pattern*, not just a rescale: the default Normalize autoscales,
    # so `values * 2` would render byte-identical.
    widget.set_image(1.0 - values)

    assert widget.image_base64 != before
    assert widget.pinned_cell == (1, 2)
    assert widget.pinned_row == 9


def test_autoscaling_is_relative(values):
    """Uniformly rescaling the data is a no-op, exactly as with imshow."""
    assert HeatmapSelect(values).image_base64 == HeatmapSelect(values * 2).image_base64
    assert (
        HeatmapSelect(values, vmin=0.0, vmax=1.0).image_base64
        != HeatmapSelect(values * 2, vmin=0.0, vmax=1.0).image_base64
    )


def test_set_image_reshapes_and_can_override_the_colormap():
    widget = HeatmapSelect(np.zeros((4, 5)))
    widget.set_image(np.zeros((7, 8)), cmap="viridis")
    assert (widget.n_rows, widget.n_cols) == (7, 8)


def test_png_dimensions_reads_the_ihdr():
    """Grid shape comes from the PNG header, so pillow isn't needed to read it."""
    buf = io.BytesIO()
    Image.new("RGB", (13, 7), "white").save(buf, format="PNG")
    assert _png_dimensions(buf.getvalue()) == (7, 13)

    with pytest.raises(ValueError, match="not a PNG"):
        _png_dimensions(b"definitely not a png")
