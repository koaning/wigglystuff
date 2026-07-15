# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "wigglystuff",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from wigglystuff import EsmWidget

    return EsmWidget, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # EsmWidget

    `EsmWidget` renders an inline [ES module](https://developer.mozilla.org/docs/Web/JavaScript/Guide/Modules)
    in the notebook. Because the module is loaded as a *real* module, top-level
    `import` statements work — so you can pull any library straight from a CDN
    (motion.dev, Observable Plot, d3, chart.js, three.js, …).

    The module follows the standard `anywidget` contract
    (`export default { render }`), and the widget hands it a two-way `data`
    traitlet. Update `data` from Python and the module sees a `change:data`
    event; it does **not** re-run `render`, so your module decides what to do —
    animation libraries can *tween* toward the new state, chart libraries can
    *redraw*.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Tween on data change — motion.dev

    A single `import` from a CDN, and the module animates the box toward
    whatever `x` Python last put in `data`. Drag the slider and watch it spring.
    """)
    return


@app.cell
def _(mo, motion_box, x_slider):
    mo.vstack([x_slider, motion_box])
    return


@app.cell
def _(EsmWidget):
    motion_box = EsmWidget(
        """
        import { animate } from "https://cdn.jsdelivr.net/npm/motion@12/+esm";
        export default {
          render({ model, el }) {
            const box = document.createElement("div");
            box.style.cssText = "width:64px;height:64px;border-radius:14px;background:#e94560;margin-top: 10px";
            el.appendChild(box);
            const draw = () => animate(
              box,
              { x: model.get("data").x, rotate: model.get("data").x },
              { type: "spring", stiffness: 120, damping: 12 },
            );
            draw();
            model.on("change:data", draw);
          }
        };
        """,
        data={"x": 0},
        width=600,
        height=100,
    )
    return (motion_box,)


@app.cell
def _(mo):
    x_slider = mo.ui.slider(0, 520, value=60, label="target x")
    return (x_slider,)


@app.cell
def _(motion_box, x_slider):
    # Updating `data` fires `change:data` in the browser; the module tweens.
    motion_box.data = {"x": x_slider.value}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Update in place — motion.dev

    A second motion.dev example: bars keep their identity across updates and
    *glide* from their current height to the new one — no rebuild from zero.
    Only newly added bars start from the bottom.
    """)
    return


@app.cell
def _(EsmWidget):
    bars_box = EsmWidget(
        """
        import { animate } from "https://cdn.jsdelivr.net/npm/motion@12/+esm";
        export default {
          render({ model, el }) {
            const row = document.createElement("div");
            row.style.cssText = "display:flex;gap:8px;align-items:flex-end;height:120px;margin-top:10px";
            el.appendChild(row);
            const bars = [];
            const draw = () => {
              const values = model.get("data").values;
              // Reconcile: add new bars (from 0), drop extras, keep the rest.
              while (bars.length < values.length) {
                const bar = document.createElement("div");
                bar.style.cssText = "width:28px;height:0px;border-radius:6px 6px 0 0;background:#e94560";
                row.appendChild(bar);
                bars.push(bar);
              }
              while (bars.length > values.length) {
                const bar = bars.pop();
                animate(bar, { height: "0px" }, { type: "spring", stiffness: 200, damping: 18 })
                  .finished.then(() => bar.remove());
              }
              // Animate each bar from its CURRENT height to the new one.
              values.forEach((v, i) => {
                animate(bars[i], { height: v + "px" }, { type: "spring", stiffness: 200, damping: 18 });
              });
            };
            draw();
            model.on("change:data", draw);
          }
        };
        """,
        data={"values": []},
        width=600,
        height=160,
    )
    bars_box
    return (bars_box,)


@app.cell
def _(mo):
    n_slider = mo.ui.slider(3, 12, value=7, label="bars")
    n_slider
    return (n_slider,)


@app.cell
def _(bars_box, n_slider):
    bars_box.data = {"values": [(i * 7 % 11 + 1) * 9 for i in range(n_slider.value)]}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Interactive sketch — p5.js

    Something Python can't do in a cell: a live p5.js sketch. The wave swells
    toward your cursor, its amplitude comes from Python via `data`, and the
    sketch pushes the mouse position back into `data` (two-way).
    """)
    return


@app.cell
def _(EsmWidget, mo):
    swell_box = EsmWidget(
        """
        import p5 from "https://cdn.jsdelivr.net/npm/p5@1/+esm";
        export default {
          render({ model, el }) {
            const holder = document.createElement("div");
            el.appendChild(holder);
            const sketch = (p) => {
              let t = 0;
              p.setup = () => {
                p.createCanvas(model.get("width"), model.get("height"));
                p.colorMode(p.HSB, 360, 100, 100);
                p.noStroke();
                // p5 reveals canvases via document.getElementsByTagName, which
                // can't see into marimo's shadow DOM — so unhide it ourselves.
                const cv = holder.querySelector("canvas");
                if (cv) { cv.removeAttribute("data-hidden"); cv.style.visibility = "visible"; }
              };
              p.draw = () => {
                p.background(230, 30, 12);
                const amp = model.get("data").amp;
                const w = p.width, h = p.height;
                for (let x = 0; x <= w; x += 12) {
                  const near = p.constrain(Math.abs(x - p.mouseX), 0, 180);
                  const bulge = p.map(near, 0, 180, amp, 0);
                  const y = h / 2 + Math.sin(x * 0.03 + t) * (amp + bulge);
                  p.fill(p.map(x, 0, w, 180, 320), 80, 95);
                  p.circle(x, y, 8);
                }
                t += 0.05;
              };
              p.mouseMoved = () => {
                // p5 fires mouseMoved for movement anywhere in the window;
                // only push mx when the cursor is actually over the canvas.
                if (p.mouseX < 0 || p.mouseX > p.width) return;
                if (p.mouseY < 0 || p.mouseY > p.height) return;
                model.set("data", {
                  ...model.get("data"),
                  mx: Math.round(p.mouseX),
                  my: Math.round(p.mouseY),
                });
                model.save_changes();
              };
            };
            const instance = new p5(sketch, holder);
            return () => instance.remove();
          }
        };
        """,
        data={"amp": 40},
        width=600,
        height=260,
    )
    # Display the *wrapped* element: in marimo, browser→Python syncs and
    # downstream reactive reads go through `mo.ui.anywidget(...)`, not the raw
    # widget. Keep `swell_box` around so the amp slider can still set `data`.
    p5_widget = mo.ui.anywidget(swell_box)
    p5_widget
    return p5_widget, swell_box


@app.cell
def _(mo):
    amp_slider = mo.ui.slider(10, 80, value=40, label="swell")
    amp_slider
    return (amp_slider,)


@app.cell
def _(amp_slider, swell_box):
    swell_box.data = {**swell_box.data, "amp": amp_slider.value}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Reading `data` back in Python

    **marimo only re-runs on events coming *from the browser*.** The wrapped
    element's value re-triggers downstream cells when the *frontend* sends an
    update — not when Python pushes one. So:

    - **Mouse move → re-runs.** The sketch pushes the mouse position (`mx`,
      `my`) into `data` from JS (`model.set(...)` + `model.save_changes()`).
      That's a browser→Python event, so the cell below re-runs and the
      coordinates track your cursor.
    - **Amp slider → does *not* re-run.** Dragging the slider is a
      Python→browser push: it updates `data.amp` and the sketch responds, but
      nothing comes back from the browser, so this cell stays put.

    To read the value back, go through the *wrapped* element — `p5_widget.data`
    (or `p5_widget.value["data"]`) — **not** the raw `swell_box`.
    """)
    return


@app.cell
def _(p5_widget):
    p5_widget.data
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    The module source can also be a local `.js` file path or an `http(s)://`
    URL — both are read/fetched in Python at construction, so the browser always
    receives plain JavaScript:

    ```python
    EsmWidget("widgets/chart.js")
    EsmWidget("https://example.com/widget.js")
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
