import marimo as mo
import pytest

import wigglystuff.hint as hint_module
from wigglystuff import Hint


@pytest.fixture
def in_notebook(monkeypatch):
    """Pretend we are inside a marimo kernel so rendering is allowed."""
    monkeypatch.setattr(hint_module, "_require_marimo_notebook", lambda: None)


def test_constructor():
    h = Hint("target", "note", side="top", color="#abc", gap=2)
    assert (h.side, h.color, h.gap) == ("top", "#abc", 2)

    # defaults: note beside the widget, arc following the notebook text colour
    default = Hint("target", "note")
    assert (default.side, default.color, default.gap) == ("right", "currentColor", 3)

    for bad in ["sideways", "TOP", "", None]:
        with pytest.raises(ValueError):
            Hint("target", "note", side=bad)


def test_requires_marimo_notebook():
    # Constructing is fine anywhere; only rendering needs a live kernel.
    h = Hint("target", "note")
    with pytest.raises(RuntimeError, match="marimo-only"):
        h._mime_()
    with pytest.raises(RuntimeError, match="marimo-only"):
        h._repr_mimebundle_()


def test_renders_and_composes(in_notebook):
    slider = mo.ui.slider(1, 10)

    mimetype, html = Hint(slider, "drag to change **N**")._mime_()
    assert mimetype == "text/html"
    # both boxes present, and the str note went through mo.md
    assert 'data-hint-box="target"' in html
    assert 'data-hint-box="note"' in html
    assert "<strong>N</strong>" in html

    # an mo.md note must render too -- interpolating it directly would emit its
    # markdown *source*, leaving literal asterisks
    assert "<strong>N</strong>" in mo.as_html(Hint(slider, mo.md("**N**"))).text

    # renders as ordinary marimo content, so it composes and nests
    assert mo.hstack([Hint(slider, "a"), Hint(slider, "b")]).text.count("data-hint-root") == 2
    assert mo.as_html(Hint(Hint(slider, "inner"), "outer")).text.count("data-hint-root") == 2
