"""WandbChart widget for live wandb run visualization."""

from pathlib import Path
from typing import Any, Optional, Sequence

import anywidget
import traitlets


class WandbChart(anywidget.AnyWidget):
    """DEPRECATED"""
    def __init__(
        self,
        *args: Sequence[Any]
        **kwargs: Any,
    ) -> None:
        """DEPRECATED"""
        print("""This widget is deprecated due to a security concern.

        When marimo does a static HTML export it will also export all the anywidget traits.
        That means we also expose the api_key in any static export. This is highly
        risky. So we decided to drop this feature alltogether.
        """)
