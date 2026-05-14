"""Public widget exports for the wigglystuff package."""

import importlib
import importlib.metadata

__version__ = importlib.metadata.version("wigglystuff")

# Maps public names to (module_path, attribute_name) for lazy loading.
_LAZY_IMPORTS = {
    "AnnotationWidget": (".annotation", "AnnotationWidget"),
    "AltairWidget": (".altair_widget", "AltairWidget"),
    "ApiDoc": (".api_doc", "ApiDoc"),
    "CellTour": (".cell_tour", "CellTour"),
    "ChartPuck": (".chart_puck", "ChartPuck"),
    "ChartMultiSelect": (".chart_multi_select", "ChartMultiSelect"),
    "ChartSelect": (".chart_select", "ChartSelect"),
    "ColorPicker": (".color_picker", "ColorPicker"),
    "CopyToClipboard": (".copy_to_clipboard", "CopyToClipboard"),
    "DiffViewer": (".diff_viewer", "DiffViewer"),
    "DriverTour": (".driver_tour", "DriverTour"),
    "EdgeDraw": (".edge_draw", "EdgeDraw"),
    "EnvConfig": (".env_config", "EnvConfig"),
    "GamepadWidget": (".gamepad", "GamepadWidget"),
    "HoverZoom": (".hover_zoom", "HoverZoom"),
    "HTMLRefreshWidget": (".html", "HTMLRefreshWidget"),
    "ImageRefreshWidget": (".html", "ImageRefreshWidget"),
    "ProgressBar": (".html", "ProgressBar"),
    "KeystrokeWidget": (".keystroke", "KeystrokeWidget"),
    "Matrix": (".matrix", "Matrix"),
    "ModuleTreeWidget": (".module_tree", "ModuleTreeWidget"),
    "Neo4jWidget": (".neo4j_widget", "Neo4jWidget"),
    "NestedTable": (".nested_table", "NestedTable"),
    "Paint": (".paint", "Paint"),
    "ParallelCoordinates": (".parallel_coords", "ParallelCoordinates"),
    "PlaySlider": (".play_slider", "PlaySlider"),
    "PulsarChart": (".pulsar_chart", "PulsarChart"),
    "ScatterWidget": ("drawdata", "ScatterWidget"),
    "Slider2D": (".slider2d", "Slider2D"),
    "SplineDraw": (".spline_draw", "SplineDraw"),
    "SortableList": (".sortable_list", "SortableList"),
    "WebkitSpeechToTextWidget": (".talk", "WebkitSpeechToTextWidget"),
    "TangleChoice": (".tangle", "TangleChoice"),
    "TangleSelect": (".tangle", "TangleSelect"),
    "TangleSlider": (".tangle", "TangleSlider"),
    "TextCompare": (".text_compare", "TextCompare"),
    "Treemap": (".treemap", "Treemap"),
    "ThreeWidget": (".three_widget", "ThreeWidget"),
    "WandbChart": (".wandb_chart", "WandbChart"),
    "forecast_chart": (".utils", "forecast_chart"),
    "WebcamCapture": (".webcam_capture", "WebcamCapture"),
}

__all__ = list(_LAZY_IMPORTS)


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        if module_path.startswith("."):
            mod = importlib.import_module(module_path, __name__)
        else:
            mod = importlib.import_module(module_path)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
