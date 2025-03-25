import marimo

__generated_with = "0.11.26"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import Draw
    from mohtml import img
    from pydantic import BaseModel
    import base64
    from io import BytesIO
    from PIL import Image
    return BaseModel, BytesIO, Draw, Image, base64, img, mo


@app.cell
def _(BytesIO, Image, base64):
    def base64_to_pil(base64_string):
        """Convert a base64 string to PIL Image"""
        # Remove the data URL prefix if it exists
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
    
        # Decode base64 string
        img_data = base64.b64decode(base64_string)
    
        # Create PIL Image from bytes
        img = Image.open(BytesIO(img_data))
        return img
    return (base64_to_pil,)


@app.cell
def _(Draw, mo):
    widget = mo.ui.anywidget(Draw(width=1000, height=450))
    return (widget,)


@app.cell
def _(widget):
    widget
    return


@app.cell
def _(img, widget):
    img(src=widget.value["base64"])
    return


@app.cell
def _(mo):
    btn = mo.ui.button(value=0, label="Parse")
    btn
    return (btn,)


@app.cell
def _(BaseModel, widget):
    import openai
    import instructor
    from dotenv import load_dotenv
    from typing import List

    load_dotenv(".env")

    client = instructor.from_openai(openai.OpenAI())

    class Edge(BaseModel):
        source: str
        target: str

    class Graph(BaseModel):
        nodes: List[str]
        edges: List[Edge]

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that can parse data from drawings"},
            {"role": "user", "content": [
                    "Here is an image that needs parsing. We want the JSON structure of out of the DAG.",  
                    instructor.Image.from_base64(widget.value["base64"]),
                ],
            },
        ],
        response_model=Graph
    )
    return Edge, Graph, List, client, instructor, load_dotenv, openai, resp


@app.cell
def _(resp):
    dict(resp)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
