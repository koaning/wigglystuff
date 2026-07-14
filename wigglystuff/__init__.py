"""Public widget exports for the wigglystuff package."""

import importlib.metadata
import tomllib
from pathlib import Path

from .annotation import AnnotationWidget
from .altair_widget import AltairWidget
from .api_doc import ApiDoc
from .bezier_curve import BezierCurve
from .cell_tour import CellTour
from .chart_puck import ChartPuck
from .chart_multi_select import ChartMultiSelect
from .chart_select import ChartSelect
from .circular_slider import CircularRangeSlider, CircularSlider
from .color_picker import ColorPicker
from .copy_to_clipboard import CopyToClipboard
from .curve_editor import CurveEditor
from .driver_tour import DriverTour
from .edge_draw import EdgeDraw
from .env_config import EnvConfig
from .excalidraw import Excalidraw
from .gamepad import GamepadWidget
from .graph_widget import GraphWidget
from .grid_draw import GridDraw
from .hover_zoom import HoverZoom
from .html import HTMLRefreshWidget, ImageRefreshWidget, ProgressBar
from .keystroke import KeystrokeWidget
from .live_edit import LiveEdit, inspect_run
from .manim_web import ManimWeb
from .matrix import Matrix
from .module_tree import ModuleTreeWidget
from .neo4j_widget import Neo4jWidget
from .nested_table import NestedTable
from .paint import Paint
from .parallel_coords import ParallelCoordinates
from .play_slider import PlaySlider
from .ridgeline_chart import RidgelineChart
from drawdata import ScatterWidget
from .slider2d import Slider2D
from .spline_draw import SplineDraw
from .sortable_list import SortableList
from .talk import WebkitSpeechToTextWidget
from .tangle import TangleChoice, TangleSelect, TangleSlider
from .text_compare import TextCompare
from .treemap import Treemap
from .three_widget import ThreeWidget
from .wandb_chart import WandbChart
from .utils import forecast_chart
from .webcam_capture import WebcamCapture

try:
    __version__ = importlib.metadata.version("wigglystuff")
except importlib.metadata.PackageNotFoundError:
    _pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    __version__ = tomllib.loads(_pyproject.read_text())["project"]["version"]

__all__ = [
    "AnnotationWidget",
    "AltairWidget",
    "ApiDoc",
    "BezierCurve",
    "CellTour",
    "ChartPuck",
    "ChartMultiSelect",
    "ChartSelect",
    "CircularRangeSlider",
    "CircularSlider",
    "ColorPicker",
    "CopyToClipboard",
    "CurveEditor",
    "DriverTour",
    "EdgeDraw",
    "EnvConfig",
    "Excalidraw",
    "GamepadWidget",
    "GraphWidget",
    "GridDraw",
    "KeystrokeWidget",
    "LiveEdit",
    "ManimWeb",
    "Matrix",
    "ModuleTreeWidget",
    "Neo4jWidget",
    "NestedTable",
    "Paint",
    "ParallelCoordinates",
    "PlaySlider",
    "RidgelineChart",
    "ScatterWidget",
    "Slider2D",
    "SplineDraw",
    "SortableList",
    "TangleChoice",
    "TangleSelect",
    "TangleSlider",
    "TextCompare",
    "Treemap",
    "WebkitSpeechToTextWidget",
    "ThreeWidget",
    "WandbChart",
    "WebcamCapture",
    "HoverZoom",
    "HTMLRefreshWidget",
    "ImageRefreshWidget",
    "ProgressBar",
    "forecast_chart",
    "inspect_run",
]
