import marimo

__generated_with = "0.18.2"
app = marimo.App(width="compact")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import MapPicker, Slider2D

    return MapPicker, Slider2D, mo


@app.cell
def _(mo):
    mo.md("""
    # MapPicker Demo
    """)
    return


@app.cell
def _(MapPicker, mo):
    widget = mo.ui.anywidget(
        MapPicker(
            lat=52.52,
            lon=13.405,
            zoom=12,
            show_marker=True,
        )
    )
    widget
    return (widget,)


@app.cell
def _(mo, widget):
    mo.callout(
        f"lat = {widget.lat:.4f}, lon = {widget.lon:.4f}, zoom = {widget.zoom:.1f}"
    )
    return


@app.cell
def _(widget):
    bbox = widget.bbox
    f"bbox: west={bbox[0]:.4f}, south={bbox[1]:.4f}, east={bbox[2]:.4f}, north={bbox[3]:.4f}"
    return


@app.cell
def _(mo):
    mo.md("""
    ## Control with Slider2D
    """)
    return


@app.cell
def _(Slider2D, mo):
    # Slider2D to control lat/lon
    # x_bounds for longitude (-180 to 180), y_bounds for latitude (-85 to 85)
    pos_slider = mo.ui.anywidget(
        Slider2D(
            x=13.405,
            y=52.52,
            x_bounds=(-180.0, 180.0),
            y_bounds=(-85.0, 85.0),
            width=300,
            height=300,
        )
    )
    return (pos_slider,)


@app.cell
def _(mo):
    # Vertical slider for zoom (2-19)
    zoom_slider = mo.ui.slider(
        start=2, stop=19, step=0.5, value=10, orientation="vertical"
    )
    return (zoom_slider,)


@app.cell
def _(mo, pos_slider, zoom_slider):
    mo.hstack([pos_slider, zoom_slider], justify="start", gap=2)
    return


@app.cell
def _(MapPicker, mo, pos_slider, zoom_slider):
    # Map controlled by sliders
    controlled_map = mo.ui.anywidget(
        MapPicker(
            lat=pos_slider.y,
            lon=pos_slider.x,
            zoom=zoom_slider.value,
            show_marker=True,
            marker_color="#ef4444",
        )
    )
    controlled_map
    return (controlled_map,)


@app.cell
def _(mo, pos_slider, zoom_slider):
    mo.callout(
        f"Position: lon = {pos_slider.x:.2f}, lat = {pos_slider.y:.2f} | Zoom = {zoom_slider.value:.1f}"
    )
    return


if __name__ == "__main__":
    app.run()
