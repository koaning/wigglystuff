"""Tests for ChartPuck widget."""

import pytest

plt = pytest.importorskip("matplotlib.pyplot")

from wigglystuff.chart_puck import ChartPuck, extract_axes_info, fig_to_base64


@pytest.fixture
def simple_figure():
    """Create a simple matplotlib figure for testing."""
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [1, 2, 3])
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    yield fig
    plt.close(fig)


def test_import_chart_puck():
    from wigglystuff.chart_puck import ChartPuck


def test_chart_puck_from_package():
    from wigglystuff import ChartPuck


def test_fig_to_base64_returns_data_url(simple_figure):
    result = fig_to_base64(simple_figure)
    assert result.startswith("data:image/png;base64,")


def test_extract_axes_info_returns_correct_types(simple_figure):
    x_bounds, y_bounds, axes_pixel_bounds, width_px, height_px = extract_axes_info(
        simple_figure
    )
    assert isinstance(x_bounds, tuple) and len(x_bounds) == 2
    assert isinstance(y_bounds, tuple) and len(y_bounds) == 2
    assert isinstance(axes_pixel_bounds, tuple) and len(axes_pixel_bounds) == 4
    assert isinstance(width_px, int)
    assert isinstance(height_px, int)


def test_extract_axes_info_respects_xlim_ylim(simple_figure):
    x_bounds, y_bounds, _, _, _ = extract_axes_info(simple_figure)
    assert x_bounds == (0.0, 4.0)
    assert y_bounds == (0.0, 4.0)


def test_chart_puck_defaults_to_center(simple_figure):
    puck = ChartPuck(simple_figure)
    # x and y are now lists
    assert puck.x == [2.0]
    assert puck.y == [2.0]


def test_chart_puck_accepts_single_initial_position(simple_figure):
    puck = ChartPuck(simple_figure, x=1.0, y=3.0)
    # Single values are converted to lists
    assert puck.x == [1.0]
    assert puck.y == [3.0]


def test_chart_puck_accepts_multiple_pucks(simple_figure):
    puck = ChartPuck(simple_figure, x=[0.5, 1.5, 2.5], y=[0.5, 1.5, 2.5])
    assert puck.x == [0.5, 1.5, 2.5]
    assert puck.y == [0.5, 1.5, 2.5]


def test_chart_puck_raises_on_mismatched_lengths(simple_figure):
    with pytest.raises(ValueError, match="same length"):
        ChartPuck(simple_figure, x=[1.0, 2.0], y=[1.0])


def test_chart_puck_has_chart_base64(simple_figure):
    puck = ChartPuck(simple_figure)
    assert puck.chart_base64.startswith("data:image/png;base64,")


def test_chart_puck_styling_defaults():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    puck = ChartPuck(fig)
    plt.close(fig)

    assert puck.puck_radius == 10
    assert puck.puck_color == "#e63946"


def test_chart_puck_custom_styling():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    puck = ChartPuck(fig, puck_radius=20, puck_color="#00ff00")
    plt.close(fig)

    assert puck.puck_radius == 20
    assert puck.puck_color == "#00ff00"
