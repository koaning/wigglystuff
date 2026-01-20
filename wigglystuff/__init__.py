"""Public widget exports for the wigglystuff package."""

import importlib.metadata

from .cell_tour import CellTour
from .chart_puck import ChartPuck
from .color_picker import ColorPicker
from .copy_to_clipboard import CopyToClipboard
from .driver_tour import DriverTour
from .edge_draw import EdgeDraw
from .env_config import EnvConfig
from .gamepad import GamepadWidget
from .html import HTMLRefreshWidget, ImageRefreshWidget, ProgressBar
from .keystroke import KeystrokeWidget
from .matrix import Matrix
from .paint import Paint
from .pulsar_chart import PulsarChart
from .slider2d import Slider2D
from .sortable_list import SortableList
from .talk import WebkitSpeechToTextWidget
from .tangle import TangleChoice, TangleSelect, TangleSlider
from .text_compare import TextCompare
from .three_widget import ThreeWidget
from .webcam_capture import WebcamCapture

__version__ = importlib.metadata.version("wigglystuff")

__all__ = [
    "CellTour",
    "ChartPuck",
    "ColorPicker",
    "CopyToClipboard",
    "DriverTour",
    "EdgeDraw",
    "EnvConfig",
    "GamepadWidget",
    "KeystrokeWidget",
    "Matrix",
    "Paint",
    "PulsarChart",
    "Slider2D",
    "SortableList",
    "TangleChoice",
    "TangleSelect",
    "TangleSlider",
    "TextCompare",
    "WebkitSpeechToTextWidget",
    "ThreeWidget",
    "WebcamCapture",
    "HTMLRefreshWidget",
    "ImageRefreshWidget",
    "ProgressBar",
]
