# /// script
# dependencies = [
#     "marimo",
#     "mohtml==0.1.11",
#     "numpy==2.4.3",
#     "pillow==12.1.1",
#     "scipy==1.17.1",
#     "wigglystuff==0.2.40",
# ]
# requires-python = ">=3.12"
# ///

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="columns", sql_output="polars")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import io
    from PIL import Image, ImageDraw
    from scipy.ndimage import map_coordinates

    return Image, ImageDraw, io, map_coordinates, mo, np


@app.cell
def _(Image, ImageDraw, io):
    def get_source_image(file_list):
        # Check if a file was actually uploaded
        if file_list:
            try:
                # upload.value is a list of marimo.ui.file.File objects
                # .contents contains the raw bytes
                return Image.open(io.BytesIO(file_list[0].contents)).convert("RGB")
            except Exception as e:
                return None

        # Fallback Placeholder: A "Frame" to make alignment obvious
        img = Image.new("RGB", (600, 600), "#fdfcf0")
        draw = ImageDraw.Draw(img)
        # Outer black border
        draw.rectangle([0, 0, 599, 599], outline="black", width=30)
        # Inner red border (The "Target" for the loop)
        draw.rectangle([200, 200, 400, 400], outline="#e74c3c", width=15)
        draw.text((260, 40), "OUTER", fill="black")
        draw.text((265, 220), "INNER", fill="#e74c3c")
        return img

    return (get_source_image,)


@app.cell
def _(mo):
    upload = mo.ui.file(kind="button", label="Upload Screenshot")
    c_re = mo.ui.slider(-7, 7.0, step=0.01, value=1.0, label="Scale ($c_{re}$)")
    c_im = mo.ui.slider(-70.0, 70.0, step=0.01, value=0.0, label="Twist ($c_{im}$)")
    zoom = mo.ui.slider(0.0, 10.0, step=0.01, value=0.0, label="Zoom Depth")
    view_mode = mo.ui.radio(["Spiral Space", "Log Space"], value="Spiral Space", label="View")
    return c_im, c_re, upload, view_mode, zoom


@app.cell
def _():
    from wigglystuff import Paint

    return (Paint,)


@app.cell
def _(Image, map_coordinates, mo, np):
    @mo.cache
    def apply_droste(img, cr, ci, z_shift, mode):
        # Convert image to numpy array for math
        arr = np.array(img)
        h, w, _ = arr.shape

        # Generate pixel grid in normalized coordinates [-1, 1]
        y, x = np.indices((h, w))
        u, v = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)

        # 1. Map to Log-Polar Space (The Top-Middle Image in the video)
        # r_log is ln(radius), theta is the angle
        r_log = 0.5 * np.log(u**2 + v**2 + 1e-9)
        theta = np.arctan2(v, u)

        # Add the Zoom Shift (traveling through the log-radius)
        r_log += z_shift * 2.0

        # 2. Apply Linear Transformation: f(z) = c * z
        # This creates the spiral/scaling effect
        z_real = cr * r_log - ci * theta
        z_imag = ci * r_log + cr * theta

        if mode == "Log Space":
            # Visualize the repeating grid
            map_x = (z_real * (w / 4)) % w
            map_y = (z_imag / (2 * np.pi) * h) % h
        else:
            # 3. Map back to Cartesian with Periodic Tiling
            # Modulo on log-radius creates the infinite nesting
            # We use % 1.0 to snap back to the outer frame once we hit the inner
            r_final = np.exp(z_real % 1.0)
            theta_final = z_imag

            map_x = (r_final * np.cos(theta_final) + 1) / 2 * w
            map_y = (r_final * np.sin(theta_final) + 1) / 2 * h

        # 4. Resample pixels using interpolation for all 3 RGB channels
        output_channels = []
        for i in range(3):
            ch = map_coordinates(arr[..., i], [map_y % h, map_x % w], order=1)
            output_channels.append(ch)

        return Image.fromarray(np.stack(output_channels, axis=-1))

    return (apply_droste,)


@app.cell
def _(apply_droste, c_im, c_re, mo, paint, upload, view_mode, zoom):
    src_img = paint.get_pil()
    res_img = apply_droste(src_img, c_re.value, c_im.value, zoom.value, view_mode.value)

    mo.md(f"""
        # 3Blue1Brown Droste Simulator
        {upload}""")
    return res_img, src_img


@app.cell
def _(Paint, get_source_image, mo, upload):
    _src_img = get_source_image(upload.value)
    paint = mo.ui.anywidget(Paint(init_image=_src_img))
    paint
    return (paint,)


@app.cell
def _(c_im, c_re, mo, view_mode, zoom):
    mo.hstack([c_re, c_im, zoom, view_mode], justify="start")
    return


@app.cell
def _(mo, res_img, src_img):
    mo.hstack([src_img, res_img], justify="start")
    return


if __name__ == "__main__":
    app.run()
