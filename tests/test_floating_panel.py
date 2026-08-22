import marimo as mo
import pytest

import wigglystuff.floating_panel as fp_module
from wigglystuff import FloatingPanel


@pytest.fixture
def in_notebook(monkeypatch):
    """Pretend we are inside a marimo kernel so rendering is allowed."""
    monkeypatch.setattr(fp_module, "_require_marimo_notebook", lambda: None)


def test_constructor():
    p = FloatingPanel("child", corner="top-left", width=240, collapsed=True)
    assert (p.corner, p.width, p.collapsed) == ("top-left", 240, True)

    # defaults: bottom-right, shrink-wrapped (width=None), expanded
    default = FloatingPanel("child")
    assert (default.corner, default.width, default.collapsed) == (
        "bottom-right",
        None,
        False,
    )

    for bad in ["middle", "TOP-LEFT", "", None]:
        with pytest.raises(ValueError):
            FloatingPanel("child", corner=bad)
    for bad in [0, -10]:
        with pytest.raises(ValueError):
            FloatingPanel("child", width=bad)


def test_requires_marimo_notebook():
    # Constructing is fine anywhere; only rendering needs a live kernel.
    p = FloatingPanel("child")
    with pytest.raises(RuntimeError, match="marimo-only"):
        p._mime_()
    with pytest.raises(RuntimeError, match="marimo-only"):
        p._repr_mimebundle_()


def test_renders_and_composes(in_notebook):
    slider = mo.ui.slider(1, 10)

    mimetype, html = FloatingPanel(slider, width=240)._mime_()
    assert mimetype == "text/html"
    # the panel root and body wrapper are present around the live child
    assert "data-fp-root" in html
    assert "data-fp-body" in html

    # renders as ordinary marimo content, so it composes inside a layout
    assert mo.hstack(
        [FloatingPanel(slider), FloatingPanel(slider)]
    ).text.count("data-fp-root") == 2
