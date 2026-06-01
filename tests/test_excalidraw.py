import json

from wigglystuff import Excalidraw

SCENE = {
    "elements": [{"id": "a", "type": "rectangle"}],
    "appState": {"viewBackgroundColor": "#ffffff"},
    "files": {},
}


def test_basic_initialization():
    """Defaults: empty scene/image, 600px tall, 1s sync throttle."""
    widget = Excalidraw()
    assert widget.scene == {}
    assert widget.image_base64 == ""
    assert widget.get_pil() is None
    assert widget.theme == "light"
    assert widget.height == 600
    assert widget.sync_throttle_ms == 1000


def test_scene_and_helpers():
    """scene= preloads the canvas and the helper accessors agree."""
    widget = Excalidraw(scene=SCENE, height=400, sync_throttle_ms=500, theme="dark")
    assert widget.scene == SCENE
    assert widget.height == 400 and widget.sync_throttle_ms == 500
    assert widget.theme == "dark"
    assert widget.get_scene() == SCENE
    assert json.loads(widget.to_json()) == SCENE


def test_save_and_from_file_round_trip(tmp_path):
    """save() writes JSON that from_file() reads back into a new widget."""
    path = tmp_path / "diagram.excalidraw"
    Excalidraw(scene=SCENE).save(path)
    loaded = Excalidraw.from_file(path, height=300)
    assert loaded.scene == SCENE
    assert loaded.height == 300
