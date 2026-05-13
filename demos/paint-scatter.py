# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pillow",
#     "wigglystuff",
# ]
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import base64
    import io
    import random

    import marimo as mo
    from PIL import Image, ImageChops, ImageDraw
    from wigglystuff import Paint

    return Image, ImageChops, ImageDraw, Paint, base64, io, mo, random


@app.cell(hide_code=True)
def _(mo):
    mo.Html("<h1>Paint base64 update demo</h1>")
    return


@app.cell
def _(Image, ImageChops, ImageDraw, base64, io, random):
    def image_to_base64(image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def blank_image(width, height):
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        draw.line([(80, 275), (170, 110), (265, 245), (405, 75)], fill="black", width=8)
        draw.arc([120, 90, 280, 250], 210, 25, fill="black", width=7)
        return image

    def blackish_points(image):
        rgb = image.convert("RGB")
        pixels = rgb.load()
        width, height = rgb.size
        points = []
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                r, g, b = pixels[x, y]
                if r < 45 and g < 45 and b < 45:
                    points.append((x, y))
        return points

    def add_pixels_near_black(image, count=150):
        result = image.convert("RGB").copy()
        draw = ImageDraw.Draw(result)
        points = blackish_points(result)
        if not points:
            return result

        width, height = result.size
        palette = [
            (31, 119, 180),
            (255, 127, 14),
            (44, 160, 44),
            (214, 39, 40),
            (148, 103, 189),
        ]
        for _ in range(count):
            x, y = random.choice(points)
            x = max(0, min(width - 1, x + random.randint(-18, 18)))
            y = max(0, min(height - 1, y + random.randint(-18, 18)))
            radius = random.choice([2, 3, 4, 6])
            color = random.choice(palette)
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=color,
            )
        return result

    def image_changed(before, after):
        return ImageChops.difference(
            before.convert("RGB"), after.convert("RGB")
        ).getbbox() is not None

    return add_pixels_near_black, blank_image, image_changed, image_to_base64


@app.cell(hide_code=True)
def _(Paint, blank_image, image_to_base64, mo):
    width = 512
    height = 384
    paint_widget = Paint(
        width=width,
        height=height,
        store_background=True,
        init_image=blank_image(width, height),
    )
    tick, set_tick = mo.state(0)
    is_playing, set_is_playing = mo.state(False)

    def play(value):
        set_is_playing(True)
        set_tick(lambda current: current + 1)
        return value + 1

    def pause(value):
        set_is_playing(False)
        return value + 1

    def reset_canvas(value):
        paint_widget.base64 = image_to_base64(blank_image(width, height))
        set_is_playing(False)
        return value + 1

    paint = mo.ui.anywidget(paint_widget)
    play_button = mo.ui.button(value=0, on_click=play, label="Play")
    pause_button = mo.ui.button(value=0, on_click=pause, label="Pause")
    reset_button = mo.ui.button(value=0, on_click=reset_canvas, label="Reset")
    auto_step = mo.ui.refresh(
        options=["1s"],
        default_interval="1s",
        label="Auto step",
    )
    return (
        auto_step,
        is_playing,
        paint,
        paint_widget,
        pause_button,
        play_button,
        reset_button,
        set_tick,
        tick,
    )


@app.cell
def _(paint):
    paint
    return


@app.cell(hide_code=True)
def _(auto_step, mo, pause_button, play_button, reset_button):
    mo.hstack([play_button, pause_button, reset_button, auto_step], justify="start")
    return


@app.cell
def _(
    add_pixels_near_black,
    auto_step,
    image_changed,
    image_to_base64,
    is_playing,
    paint_widget,
    set_tick,
    tick,
):
    _ = auto_step.value
    step = tick()
    if is_playing() and step > 0:
        start_base64 = paint_widget.base64
        start_image = paint_widget.get_pil().convert("RGB")
        current_image = paint_widget.get_pil().convert("RGB")
        if paint_widget.base64 == start_base64 and not image_changed(start_image, current_image):
            next_image = add_pixels_near_black(start_image)
            paint_widget.base64 = image_to_base64(next_image)
            set_tick(lambda current: current + 1)
    return


@app.cell(hide_code=True)
def _(is_playing, mo, tick):
    status = "playing" if is_playing() else "paused"
    mo.md(f"Status: **{status}** · step `{tick()}`")
    return


if __name__ == "__main__":
    app.run()
