# AttractorWidget API

The rendering pipeline (per-iteration distance → phase colorscale, additive
RGB+count accumulation, YUV-space tonemap) is adapted from Ricky Reusser's
[Clifford and de Jong Attractors: Revised coloring](https://observablehq.com/@rreusser/clifford-and-de-jong-attractors-revised-coloring).

::: wigglystuff.attractor.AttractorWidget

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `x_expr` | `str` | Expression for the next `x` value. May reference `x`, `y`, `pi`, `e`, any key in `params`, and whitelisted math functions. |
| `y_expr` | `str` | Expression for the next `y` value, same rules as `x_expr`. |
| `params` | `dict[str, float]` | Named scalar parameters referenced by the expressions. Keys must be valid identifiers and must not collide with reserved names (`x`, `y`, `pi`, `e`, or any math function). |
| `n_points` | `int` | Number of trajectory points iterated per frame. Clamped to `[1_000, 1_500_000]`. |
| `iterations_per_frame` | `int` | Extra iteration passes per animation frame, ≥ 1. |
| `view` | `tuple[float, float, float, float]` | `(xmin, xmax, ymin, ymax)` world bounds; defaults to `(-2.5, 2.5, -2.5, 2.5)`. Mutated by canvas drag (pan) and wheel (zoom); also writable from Python. |
| `colormap` | `str` | `"phase"` (default) uses the per-iteration-distance phase coloring. `"magma"`, `"viridis"`, `"inferno"`, `"plasma"`, `"grayscale"` use density-only LUTs and ignore `color_speed` / `color_phase`. |
| `color_speed` | `float` | How quickly hue cycles with per-iteration distance. `0.0` collapses to a single hue. `"phase"` mode only. Default `0.22`. |
| `color_phase` | `float` | Hue rotation in degrees. `"phase"` mode only. Default `180.0`. |
| `background` | `str` | One of `"black"`, `"white"`. |
| `width` | `int` | Canvas width in pixels. |
| `height` | `int` | Canvas height in pixels. |

## Whitelisted formula grammar

- Numbers, parentheses, `+ - * /`, `^` (right-associative power), unary `-`.
- Variables: `x`, `y`.
- Constants: `pi`, `e`.
- Functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `exp`, `log`, `sqrt`, `abs`, `floor`, `sign`, `min`, `max`, `pow`.
- Any other identifier must appear as a key in `params`.

## Classmethods

| Method | Description |
| --- | --- |
| `AttractorWidget.clifford(a, b, c, d, **kw)` | Preset for the Clifford attractor `x ← sin(a·y) + c·cos(a·x)`, `y ← sin(b·x) + d·cos(b·y)`. |
| `AttractorWidget.de_jong(a, b, c, d, **kw)` | Preset for the De Jong attractor `x ← sin(a·y) − cos(b·x)`, `y ← sin(c·x) − cos(d·y)`. |

## Rendering backends

The widget tries to acquire a WebGL2 context with the `EXT_color_buffer_float`
extension on first render. If both are available it iterates the system on the
GPU (state-texture ping-pong, additive accumulation, log-density tonemap). If
WebGL2 or the float extension is unavailable it falls back to a Canvas2D path
that iterates in JavaScript and accumulates into a `Uint32Array`. A small badge
in the bottom-right of the canvas reads `gpu` or `cpu` so you can tell which
backend is active.
