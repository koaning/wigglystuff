"""Public widget exports for the wigglystuff package."""

import importlib.metadata

from .annotation import AnnotationWidget
from .altair_widget import AltairWidget
from .api_doc import ApiDoc
from .cell_tour import CellTour
from .chart_puck import ChartPuck
from .chart_multi_select import ChartMultiSelect
from .chart_select import ChartSelect
from .color_picker import ColorPicker
from .copy_to_clipboard import CopyToClipboard
from .diff_viewer import DiffViewer
from .driver_tour import DriverTour
from .edge_draw import EdgeDraw
from .env_config import EnvConfig
from .gamepad import GamepadWidget
from .html import HTMLRefreshWidget, ImageRefreshWidget, ProgressBar
from .keystroke import KeystrokeWidget
from .matrix import Matrix
from .module_tree import ModuleTreeWidget
from .neo4j_widget import Neo4jWidget
from .paint import Paint
from .parallel_coords import ParallelCoordinates
from .play_slider import PlaySlider
from .pulsar_chart import PulsarChart
from drawdata import ScatterWidget
from .slider2d import Slider2D
from .spline_draw import SplineDraw
from .sortable_list import SortableList
from .talk import WebkitSpeechToTextWidget
from .tangle import TangleChoice, TangleSelect, TangleSlider
from .text_compare import TextCompare
from .three_widget import ThreeWidget
from .wandb_chart import WandbChart
from .webcam_capture import WebcamCapture

__version__ = importlib.metadata.version("wigglystuff")

__all__ = [
    "AnnotationWidget",
    "AltairWidget",
    "ApiDoc",
    "CellTour",
    "ChartPuck",
    "ChartMultiSelect",
    "ChartSelect",
    "ColorPicker",
    "CopyToClipboard",
    "DiffViewer",
    "DriverTour",
    "EdgeDraw",
    "EnvConfig",
    "GamepadWidget",
    "KeystrokeWidget",
    "Matrix",
    "ModuleTreeWidget",
    "Neo4jWidget",
    "Paint",
    "ParallelCoordinates",
    "PlaySlider",
    "PulsarChart",
    "ScatterWidget",
    "Slider2D",
    "SplineDraw",
    "SortableList",
    "TangleChoice",
    "TangleSelect",
    "TangleSlider",
    "TextCompare",
    "WebkitSpeechToTextWidget",
    "ThreeWidget",
    "WandbChart",
    "WebcamCapture",
    "HTMLRefreshWidget",
    "ImageRefreshWidget",
    "ProgressBar",
]
