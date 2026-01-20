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


def test_chart_puck_importable():
    from wigglystuff import ChartPuck


def test_extract_axes_info_respects_xlim_ylim(simple_figure):
    x_bounds, y_bounds, _, _, _ = extract_axes_info(simple_figure)
    assert x_bounds == (0.0, 4.0)
    assert y_bounds == (0.0, 4.0)


def test_chart_puck_single_puck_defaults_to_center(simple_figure):
    puck = ChartPuck(simple_figure)
    assert puck.x == [2.0]
    assert puck.y == [2.0]
    assert puck.chart_base64.startswith("data:image/png;base64,")


def test_chart_puck_multiple_pucks(simple_figure):
    puck = ChartPuck(simple_figure, x=[0.5, 1.5, 2.5], y=[0.5, 1.5, 2.5])
    assert puck.x == [0.5, 1.5, 2.5]
    assert puck.y == [0.5, 1.5, 2.5]


def test_chart_puck_raises_on_mismatched_lengths(simple_figure):
    with pytest.raises(ValueError, match="same length"):
        ChartPuck(simple_figure, x=[1.0, 2.0], y=[1.0])


def test_from_callback_creates_widget_and_updates():
    call_count = [0]

    def draw_fn(ax, x, y):
        call_count[0] += 1
        ax.scatter([x], [y])

    puck = ChartPuck.from_callback(
        draw_fn=draw_fn,
        x_bounds=(0, 10),
        y_bounds=(0, 10),
    )

    assert puck.x == [5.0]  # defaults to center
    assert puck.y == [5.0]
    initial_base64 = puck.chart_base64

    # Simulate puck movement - should trigger redraw
    puck.x = [3.0]
    assert puck.chart_base64 != initial_base64


def test_export_kmeans(simple_figure):
    sklearn = pytest.importorskip("sklearn")
    puck = ChartPuck(simple_figure, x=[1.0, 3.0], y=[1.0, 3.0])
    kmeans = puck.export_kmeans()

    assert kmeans.n_clusters == 2
    assert kmeans.init.tolist() == [[1.0, 1.0], [3.0, 3.0]]
