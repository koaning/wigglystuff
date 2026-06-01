import anywidget
import traitlets
import json
from pathlib import Path

_STATIC = Path(__file__).parent / "static"


def _path_to_json(path: Path, widget) -> dict | None:
    if path is None:
        return None
    contents = path.read_text(encoding="utf-8") if path.exists() else ""
    return {"name": path.name, "contents": contents}

def _path_from_json(value, widget) -> Path | None:
    return widget.path


class ExcalidrawWidget(anywidget.AnyWidget):
    _esm = (_STATIC / "excalidraw.js").read_text()
    _css = (_STATIC / "excalidraw.css").read_text()

    path = traitlets.Instance(Path, allow_none=True).tag(
        sync=True,
        to_json=_path_to_json,
        from_json=_path_from_json,
    )
    scene = traitlets.Dict({}).tag(sync=True)
    auto_save = traitlets.Bool(False)

    @traitlets.observe("scene")
    def _on_scene_change(self, change: dict) -> None:
        if self.auto_save and change["new"] and self.path is not None:
            self.path.write_text(json.dumps(change["new"]), encoding="utf-8")

    def __init__(self, path: Path | str | None = None, auto_save: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.path = Path(path) if isinstance(path, str) else path
        self.auto_save = auto_save
