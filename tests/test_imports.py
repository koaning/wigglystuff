"""Test that all widgets can be imported."""


def test_import_altair_widget():
    from wigglystuff.altair_widget import AltairWidget


def test_import_cell_tour():
    from wigglystuff.cell_tour import CellTour


def test_import_bezier_curve():
    from wigglystuff.bezier_curve import BezierCurve


def test_import_color_picker():
    from wigglystuff.color_picker import ColorPicker


def test_import_copy_to_clipboard():
    from wigglystuff.copy_to_clipboard import CopyToClipboard


def test_import_driver_tour():
    from wigglystuff.driver_tour import DriverTour


def test_import_edge_draw():
    from wigglystuff.edge_draw import EdgeDraw


def test_import_gamepad():
    from wigglystuff.gamepad import GamepadWidget


def test_import_graph_widget():
    from wigglystuff.graph_widget import GraphWidget


def test_import_grid_draw():
    from wigglystuff.grid_draw import GridDraw


def test_import_keystroke():
    from wigglystuff.keystroke import KeystrokeWidget


def test_import_live_edit():
    from wigglystuff.live_edit import LiveEdit, inspect_run


def test_import_matrix():
    from wigglystuff.matrix import Matrix


def test_import_paint():
    from wigglystuff.paint import Paint


def test_import_slider2d():
    from wigglystuff.slider2d import Slider2D


def test_import_sortable_list():
    from wigglystuff.sortable_list import SortableList


def test_import_tangle_choice():
    from wigglystuff.tangle import TangleChoice


def test_import_tangle_select():
    from wigglystuff.tangle import TangleSelect


def test_import_tangle_slider():
    from wigglystuff.tangle import TangleSlider


def test_import_talk():
    from wigglystuff.talk import WebkitSpeechToTextWidget


def test_import_scatter_widget():
    from wigglystuff.scatter_widget import ScatterWidget


def test_import_three_widget():
    from wigglystuff.three_widget import ThreeWidget


def test_no_unexpected_dependencies():
    """Guard against accidentally adding dependencies to pyproject.toml."""
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    deps = {
        d.split(">")[0].split("<")[0].split("=")[0].split("[")[0].strip()
        for d in data["project"]["dependencies"]
    }
    allowed = {"anywidget", "drawdata"}
    assert deps == allowed, f"Unexpected dependencies: {deps - allowed}"


def test_requires_python_matches_tomllib_availability():
    """tomllib is stdlib only from 3.11; __init__.py imports it (issue #267)."""
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())
    assert data["project"]["requires-python"] == ">=3.11"
