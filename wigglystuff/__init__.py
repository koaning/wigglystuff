"""Public widget exports for the wigglystuff package."""

from .cell_tour import CellTour
from .color_picker import ColorPicker
from .copy_to_clipboard import CopyToClipboard
from .driver_tour import DriverTour
from .edge_draw import EdgeDraw
from .gamepad import GamepadWidget
from .keystroke import KeystrokeWidget
from .matrix import Matrix
from .paint import Paint
from .slider2d import Slider2D
from .sortable_list import SortableList
from .tangle import TangleChoice, TangleSelect, TangleSlider
from .talk import WebkitSpeechToTextWidget
from .three_widget import ThreeWidget
from .webcam_capture import WebcamCapture

__all__ = [
    "CellTour",
    "ColorPicker",
    "CopyToClipboard",
    "DriverTour",
    "EdgeDraw",
    "GamepadWidget",
    "KeystrokeWidget",
    "Matrix",
    "Paint",
    "Slider2D",
    "SortableList",
    "TangleChoice",
    "TangleSelect",
    "TangleSlider",
    "WebkitSpeechToTextWidget",
    "ThreeWidget",
    "WebcamCapture",
]
