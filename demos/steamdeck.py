# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "marimo",
#     "mohtml",
#     "wigglystuff==0.4.1",
# ]
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import AnnotationWidget, KeystrokeWidget

    return AnnotationWidget, KeystrokeWidget, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Annotating from a Steam Deck

    The Steam Deck makes a surprisingly nice annotation console. With **Steam
    Input** you can bind any button on the Deck — including the d-pad and the
    four back-grip buttons — to an arbitrary keyboard key. Those keys arrive
    in the browser as ordinary `KeyboardEvent`s, which means two `wigglystuff`
    widgets can pick them up without any extra glue:

    - `KeystrokeWidget` lets you *see* what key a given button emits — handy
      while you're wiring up the Deck's button bindings.
    - `AnnotationWidget` lets you *act* on those keys through its
      `keyboard_mapping` traitlet, driving an accept / fail / defer / previous
      flow without touching the laptop's keyboard.

    The two widgets are independent — this notebook demos each in its own
    section.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Section 1 — What is the Deck sending?

    Bind a button on the Deck to a keyboard key in Steam Input, click the
    panel below to give it focus, then press the button. The widget reports
    `key`, `code`, and any modifiers — exactly what `KeyboardEvent` would
    show for that key on a regular keyboard.
    """)
    return


@app.cell
def _(KeystrokeWidget, mo):
    listener = mo.ui.anywidget(KeystrokeWidget())
    listener
    return (listener,)


@app.cell
def _(listener, mo):
    info = listener.last_key or {}
    modifiers = [
        label
        for key, label in [
            ("ctrlKey", "Ctrl"),
            ("shiftKey", "Shift"),
            ("altKey", "Alt"),
            ("metaKey", "Meta"),
        ]
        if info.get(key)
    ]
    shortcut = " + ".join(modifiers + [info.get("key", "—")]).strip(" + ")
    mo.md(
        f"**Last key:** `{shortcut or '—'}` &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"**Code:** `{info.get('code', '—')}`"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Section 2 — Annotating with the Deck

    Once you know which keys the Deck's buttons emit, point them at
    `AnnotationWidget`. The mapping below puts the four labels on the
    **arrow keys** — which makes the Deck's d-pad a natural fit — and
    binds **spacebar** to the voice-input mic toggle for free-form notes.

    | Key | Action |
    | --- | --- |
    | `↑` | accept |
    | `↓` | fail |
    | `←` | previous |
    | `→` | defer |
    | `space` | toggle voice notes |
    """)
    return


@app.cell
def _(mo):
    examples = [
        "The food was absolutely delicious and the service was top notch.",
        "Terrible experience. The waiter was rude and the steak was overcooked.",
        "It was okay, nothing special. Might come back if nothing else is open.",
        "Best pizza I've ever had! Will definitely return.",
        "The ambiance was nice but the food took forever to arrive.",
    ]
    get_index, set_index = mo.state(0)
    get_annotations, set_annotations = mo.state({})
    get_last_ts, set_last_ts = mo.state(0.0)
    return (
        examples,
        get_annotations,
        get_index,
        get_last_ts,
        set_annotations,
        set_index,
        set_last_ts,
    )


@app.cell
def _(AnnotationWidget, mo):
    annot_widget = mo.ui.anywidget(
        AnnotationWidget(
            keyboard_mapping={
                "arrowup": "accept",
                "arrowdown": "fail",
                "arrowleft": "previous",
                "arrowright": "defer",
                " ": "mic",
            },
            show_save=False,
            width=600,
        )
    )
    return (annot_widget,)


@app.cell
def _(
    annot_widget,
    examples,
    get_annotations,
    get_index,
    get_last_ts,
    set_annotations,
    set_index,
    set_last_ts,
):
    # Marimo re-runs this cell on *any* traitlet change, including each
    # streamed speech token writing to `note`. Gate on `action_timestamp`
    # so we only commit when the user actually presses an action button.
    ts = annot_widget.action_timestamp
    if ts > get_last_ts():
        set_last_ts(ts)
        action = annot_widget.action
        note = annot_widget.note
        _i = get_index()
        _annots = get_annotations()

        if action in ("accept", "fail", "defer"):
            set_annotations({**_annots, _i: {"label": action, "note": note}})
            if _i < len(examples) - 1:
                set_index(_i + 1)
        elif action == "previous":
            if _i > 0:
                set_index(_i - 1)
    return


@app.cell
def _(annot_widget, examples, get_index, mo):
    _i = get_index()
    current = examples[_i] if _i < len(examples) else "All examples labeled!"
    mo.vstack(
        [
            mo.md(f"**Example {_i + 1} of {len(examples)}**"),
            mo.md(f"> {current}"),
            annot_widget,
        ]
    )
    return


@app.cell
def _(examples, get_annotations, mo):
    _annots = get_annotations()
    rows = [
        {
            "index": idx,
            "text": text[:60] + ("..." if len(text) > 60 else ""),
            "label": _annots.get(idx, {}).get("label", ""),
            "note": _annots.get(idx, {}).get("note", ""),
        }
        for idx, text in enumerate(examples)
    ]
    mo.md(
        "### Annotations so far\n\n"
        + mo.as_html(mo.ui.table(rows, selection=None)).text
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Wiring up Steam Input

    On the Deck (or any Steam controller paired with a desktop):

    1. Switch the Deck to **desktop mode** and open Steam.
    2. Open **Settings → Controller** and make sure Steam Input is enabled
       for the active layout.
    3. Edit the layout for your browser (or use a global layout). The
       **d-pad** is the obvious fit here — bind it to the four arrow keys
       (most default desktop layouts already do this) and the accept /
       fail / previous / defer actions just work. Bind a spare button —
       e.g. one of the back grips — to **spacebar** for voice notes.
    4. Open this notebook in the Deck's browser, click the annotation
       widget once to give it focus, and start labeling.

    Use Section 1 above any time you're unsure which key a given button is
    emitting.
    """)
    return


if __name__ == "__main__":
    app.run()
