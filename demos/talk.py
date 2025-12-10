import marimo

__generated_with = "0.17.8"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Speech to Text

    You can use the free webkit API in your browser to transcribe audio live! Not every browser may support this but it is a very easy way to talk and pass the transcription to Python.
    """)
    return


@app.cell
def _(mo):
    from wigglystuff import WebkitSpeechToTextWidget

    speech_widget = mo.ui.anywidget(WebkitSpeechToTextWidget())
    speech_widget
    return (speech_widget,)


@app.cell
def _(speech_widget):
    speech_widget.transcript
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can also choose to trigger the recording from Python. Use the following two buttons.
    """)
    return


@app.cell
def _(mo, speech_widget):
    def record(boolean):
        def inner(_):
            speech_widget.listening = boolean

        return inner

    btn_start = mo.ui.button(label="Start Recording", on_click=record(True))
    btn_stop = mo.ui.button(label="End Recording", on_click=record(False))

    mo.hstack([btn_start, btn_stop])
    return


if __name__ == "__main__":
    app.run()
