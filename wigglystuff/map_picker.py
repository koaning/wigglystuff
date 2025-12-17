from pathlib import Path
from typing import Any

import anywidget
import traitlets


class MapPicker(anywidget.AnyWidget):
    """Interactive map widget for picking geographic coordinates.

    Parameters
    ----------
    lat:
        Initial latitude. Defaults to 52.52 (Berlin).
    lon:
        Initial longitude. Defaults to 13.405 (Berlin).
    zoom:
        Initial zoom level (2-19). Defaults to 12.
    show_marker:
        Whether to show a center marker pin. Defaults to False.
    marker_color:
        Color of the marker pin (hex). Defaults to blue (#3b82f6).
    """

    _esm = Path(__file__).parent / "static" / "map-picker.js"
    _css = Path(__file__).parent / "static" / "map-picker.css"

    lat = traitlets.Float(52.52).tag(sync=True)
    lon = traitlets.Float(13.405).tag(sync=True)
    zoom = traitlets.Float(12.0).tag(sync=True)
    bbox = traitlets.List(traitlets.Float(), default_value=[0.0, 0.0, 0.0, 0.0]).tag(
        sync=True
    )
    marker_color = traitlets.Unicode("#3b82f6").tag(sync=True)
    show_marker = traitlets.Bool(False).tag(sync=True)

    def __init__(
        self,
        lat: float = 52.52,
        lon: float = 13.405,
        zoom: float = 12.0,
        show_marker: bool = False,
        marker_color: str = "#3b82f6",
        **kwargs: Any,
    ) -> None:
        """Create a MapPicker widget.

        Args:
            lat: Initial latitude.
            lon: Initial longitude.
            zoom: Initial zoom level (2-19).
            show_marker: Whether to show the center marker pin.
            marker_color: Color of the marker pin (hex).
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(
            lat=lat,
            lon=lon,
            zoom=zoom,
            show_marker=show_marker,
            marker_color=marker_color,
            **kwargs,
        )

    @traitlets.validate("zoom")
    def _valid_zoom(self, proposal: dict[str, Any]) -> float:
        """Ensure zoom is within valid range."""
        zoom = proposal["value"]
        if zoom < 2 or zoom > 19:
            raise traitlets.TraitError("Zoom must be between 2 and 19.")
        return zoom

    @traitlets.validate("lat")
    def _valid_lat(self, proposal: dict[str, Any]) -> float:
        """Ensure latitude is within valid range."""
        lat = proposal["value"]
        if lat < -85 or lat > 85:
            raise traitlets.TraitError("Latitude must be between -85 and 85.")
        return lat

    @traitlets.validate("lon")
    def _valid_lon(self, proposal: dict[str, Any]) -> float:
        """Ensure longitude is within valid range."""
        lon = proposal["value"]
        if lon < -180 or lon > 180:
            raise traitlets.TraitError("Longitude must be between -180 and 180.")
        return lon

    @property
    def coords(self) -> tuple[float, float]:
        """Return current coordinates as (lat, lon) tuple."""
        return (self.lat, self.lon)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Return current bounding box as (west, south, east, north) tuple."""
        return (self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3])
