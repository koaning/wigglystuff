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


@app.cell(hide_code=True)
def _(mo):
    mo.Html(
        "<h1>Game of Life on the canvas</h1>"
        "<p>Same <code>Paint</code> + <code>mo.ui.refresh</code> technique as above, "
        "but each tick steps Conway's rules over a coarse grid of cells. Every living "
        "cell carries an RGB color that drifts toward the mean of its live neighbors "
        "with a touch of noise, so painted strokes evolve into colorful organisms. "
        "Paint on the canvas while it runs to inject new seeds.</p>"
    )
    return


@app.cell
def _(Image, ImageDraw, random):
    GOL_WIDTH = 512
    GOL_HEIGHT = 384
    CELL_PX = 8
    COLS = GOL_WIDTH // CELL_PX
    ROWS = GOL_HEIGHT // CELL_PX
    PALETTE = [
        (31, 119, 180),
        (255, 127, 14),
        (44, 160, 44),
        (214, 39, 40),
        (148, 103, 189),
    ]

    def neighbors(r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                yield (r + dr) % ROWS, (c + dc) % COLS

    def step_grid(grid):
        candidates = set(grid)
        for cell in list(grid):
            for nb in neighbors(*cell):
                candidates.add(nb)
        next_grid = {}
        for cell in candidates:
            live = [grid[nb] for nb in neighbors(*cell) if nb in grid]
            n = len(live)
            alive_now = cell in grid
            if not ((alive_now and n in (2, 3)) or (not alive_now and n == 3)):
                continue
            colors = live + ([grid[cell]] if alive_now else [])
            mr = sum(c[0] for c in colors) // len(colors)
            mg = sum(c[1] for c in colors) // len(colors)
            mb = sum(c[2] for c in colors) // len(colors)
            next_grid[cell] = (
                max(0, min(255, mr + random.randint(-12, 12))),
                max(0, min(255, mg + random.randint(-12, 12))),
                max(0, min(255, mb + random.randint(-12, 12))),
            )
        return next_grid

    def seed_grid_from_image(image):
        rgb = image.convert("RGB")
        pixels = rgb.load()
        grid = {}
        for r in range(ROWS):
            for c in range(COLS):
                rs = gs = bs = count = 0
                for y in range(r * CELL_PX, (r + 1) * CELL_PX):
                    for x in range(c * CELL_PX, (c + 1) * CELL_PX):
                        pr, pg, pb = pixels[x, y]
                        # Any pixel that's meaningfully darker than the
                        # white background in at least one channel — so
                        # colored strokes (red, orange, blue, …) also seed.
                        if min(pr, pg, pb) < 215:
                            rs += pr
                            gs += pg
                            bs += pb
                            count += 1
                if count:
                    grid[(r, c)] = (rs // count, gs // count, bs // count)
        return grid

    def default_seed():
        grid = {}
        # Glider drifting south-east
        for dr, dc in [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:
            grid[(4 + dr, 6 + dc)] = PALETTE[0]
        # Block still-life (stable, proves the rules)
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            grid[(6 + dr, 22 + dc)] = PALETTE[1]
        # R-pentomino (famously chaotic for ~1100 generations)
        for dr, dc in [(0, 1), (0, 2), (1, 0), (1, 1), (2, 1)]:
            grid[(22 + dr, 34 + dc)] = PALETTE[2]
        # Second glider drifting north-west
        for dr, dc in [(0, 1), (1, 0), (2, 0), (2, 1), (2, 2)]:
            grid[(36 + dr, 50 + dc)] = PALETTE[3]
        return grid

    def grid_to_image(grid):
        img = Image.new("RGB", (GOL_WIDTH, GOL_HEIGHT), "white")
        draw = ImageDraw.Draw(img)
        for (r, c), color in grid.items():
            x0 = c * CELL_PX
            y0 = r * CELL_PX
            draw.rectangle(
                [x0, y0, x0 + CELL_PX - 1, y0 + CELL_PX - 1],
                fill=color,
            )
        return img

    return (
        GOL_HEIGHT,
        GOL_WIDTH,
        default_seed,
        grid_to_image,
        seed_grid_from_image,
        step_grid,
    )


@app.cell(hide_code=True)
def _(
    GOL_HEIGHT,
    GOL_WIDTH,
    Paint,
    default_seed,
    grid_to_image,
    image_to_base64,
    mo,
    seed_grid_from_image,
):
    gol_paint_widget = Paint(
        width=GOL_WIDTH,
        height=GOL_HEIGHT,
        store_background=True,
        init_image=grid_to_image(default_seed()),
    )
    gol_state = {"grid": default_seed()}
    gol_tick, gol_set_tick = mo.state(0)
    gol_is_playing, gol_set_is_playing = mo.state(False)

    def gol_play(value):
        gol_set_is_playing(True)
        gol_set_tick(lambda current: current + 1)
        return value + 1

    def gol_pause(value):
        gol_set_is_playing(False)
        return value + 1

    def gol_reset(value):
        gol_state["grid"] = default_seed()
        gol_paint_widget.base64 = image_to_base64(grid_to_image(gol_state["grid"]))
        gol_set_is_playing(False)
        return value + 1

    def gol_seed_from_canvas(value):
        gol_state["grid"] = seed_grid_from_image(gol_paint_widget.get_pil())
        gol_paint_widget.base64 = image_to_base64(grid_to_image(gol_state["grid"]))
        return value + 1

    gol_paint = mo.ui.anywidget(gol_paint_widget)
    gol_play_button = mo.ui.button(value=0, on_click=gol_play, label="Play")
    gol_pause_button = mo.ui.button(value=0, on_click=gol_pause, label="Pause")
    gol_reset_button = mo.ui.button(value=0, on_click=gol_reset, label="Reset")
    gol_seed_button = mo.ui.button(
        value=0, on_click=gol_seed_from_canvas, label="Seed from canvas"
    )
    gol_auto_step = mo.ui.refresh(
        options=["100ms", "200ms", "500ms", "1s"],
        default_interval="200ms",
        label="Auto step",
    )
    return (
        gol_auto_step,
        gol_is_playing,
        gol_paint,
        gol_paint_widget,
        gol_pause_button,
        gol_play_button,
        gol_reset_button,
        gol_seed_button,
        gol_set_tick,
        gol_state,
        gol_tick,
    )


@app.cell
def _(gol_paint):
    gol_paint
    return


@app.cell(hide_code=True)
def _(
    gol_auto_step,
    gol_pause_button,
    gol_play_button,
    gol_reset_button,
    gol_seed_button,
    mo,
):
    mo.hstack(
        [
            gol_play_button,
            gol_pause_button,
            gol_reset_button,
            gol_seed_button,
            gol_auto_step,
        ],
        justify="start",
    )
    return


@app.cell
def _(
    gol_auto_step,
    gol_is_playing,
    gol_paint_widget,
    gol_set_tick,
    gol_state,
    gol_tick,
    grid_to_image,
    image_changed,
    image_to_base64,
    seed_grid_from_image,
    step_grid,
):
    _ = gol_auto_step.value
    _step_num = gol_tick()
    if gol_is_playing() and _step_num > 0:
        _start_base64 = gol_paint_widget.base64
        _start_canvas = gol_paint_widget.get_pil().convert("RGB")
        _current_canvas = gol_paint_widget.get_pil().convert("RGB")
        if (
            gol_paint_widget.base64 == _start_base64
            and not image_changed(_start_canvas, _current_canvas)
        ):
            _expected = grid_to_image(gol_state["grid"])
            if image_changed(_expected, _start_canvas):
                _painted = seed_grid_from_image(_start_canvas)
                _merged = dict(gol_state["grid"])
                _merged.update(_painted)
                gol_state["grid"] = _merged
            gol_state["grid"] = step_grid(gol_state["grid"])
            gol_paint_widget.base64 = image_to_base64(grid_to_image(gol_state["grid"]))
            gol_set_tick(lambda current: current + 1)
    return


@app.cell(hide_code=True)
def _(gol_is_playing, gol_state, gol_tick, mo):
    gol_status = "playing" if gol_is_playing() else "paused"
    mo.md(
        f"Status: **{gol_status}** · generation `{gol_tick()}` · "
        f"alive `{len(gol_state['grid'])}`"
    )
    return


if __name__ == "__main__":
    app.run()
