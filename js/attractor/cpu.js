// CPU fallback for AttractorWidget. Mirrors the GPU pipeline:
//   - per-particle iteration produces a "dist" = length(new - prev)
//   - color = phase colorscale(dist * color_speed, color_phase)
//   - accumulate (count, sum_r, sum_g, sum_b) per pixel
//   - tonemap via Reusser's YUV-space mix.

import { compileStep } from "./parser.js";
import { colormapRGB } from "./colormaps.js";

const PI2 = Math.PI * 2;

function colorscale(t, phaseRad) {
  return [
    0.5 + 0.5 * Math.cos(PI2 * t - phaseRad),
    0.5 + 0.5 * Math.cos(PI2 * (t - 1 / 3) - phaseRad),
    0.5 + 0.5 * Math.cos(PI2 * (t - 2 / 3) - phaseRad),
  ];
}

function rgb2yuv(r, g, b) {
  const y = 0.299 * r + 0.587 * g + 0.114 * b;
  return [y, 0.493 * (b - y), 0.877 * (r - y)];
}
function yuv2rgb(y, u, v) {
  return [
    y + (1 / 0.877) * v,
    y - 0.39393 * u - 0.58081 * v,
    y + (1 / 0.493) * u,
  ];
}
function smoothLimit(x, k) {
  x = 2 * x - 1;
  const a = Math.pow(Math.abs(x), 1 / k);
  return Math.sign(x) * Math.pow(a / (a + 1), k) * 0.5 + 0.5;
}

export class CPURenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = null;          // Float32Array of length n*2 (positions)
    this.accum = null;          // Float32Array of length w*h*4 (count, sum_r, sum_g, sum_b)
    this.image = null;          // ImageData (RGBA8)
    this.view = [-2.5, 2.5, -2.5, 2.5];
    this.params = {};
    this.step = null;
    this.n = 0;
    this.iterationsPerFrame = 1;
    this.colormap = "phase";
    this.colorSpeed = 0.22;
    this.colorPhase = 180.0; // degrees
    this.background = "black";
    this.totalSamples = 0;
    this._rafId = null;
    this._lastFrameMs = 0;
    this._effectiveN = 0;
    this.resize(canvas.width, canvas.height);
  }

  resize(w, h) {
    this.canvas.width = w;
    this.canvas.height = h;
    this.accum = new Float32Array(w * h * 4);
    this.image = this.ctx.createImageData(w, h);
    this.totalSamples = 0;
  }

  setExprs(xExpr, yExpr) {
    const names = Object.keys(this.params);
    this.step = compileStep(xExpr, yExpr, names);
    this.clear();
  }
  setParams(params) {
    this.params = { ...params };
    this.clear();
  }
  setView(view) {
    this.view = view.slice();
    this.clear();
  }
  setNPoints(n) {
    this.n = n;
    this._effectiveN = n;
    this.state = new Float32Array(n * 2);
    this._seed();
    this._clearAccum();
  }
  setColorSpeed(v) { this.colorSpeed = v; this._clearAccum(); }
  setColorPhase(deg) { this.colorPhase = deg; this._clearAccum(); }
  setColormap(name) { this.colormap = name; }
  setBackground(bg) { this.background = bg; }
  setIterationsPerFrame(k) { this.iterationsPerFrame = Math.max(1, k | 0); }

  clear() {
    this._seed();
    this._clearAccum();
  }

  _clearAccum() {
    this.accum.fill(0);
    this.totalSamples = 0;
  }

  _seed() {
    if (!this.state) return;
    const [xmin, xmax, ymin, ymax] = this.view;
    const dx = xmax - xmin;
    const dy = ymax - ymin;
    for (let i = 0; i < this.state.length; i += 2) {
      this.state[i] = xmin + Math.random() * dx;
      this.state[i + 1] = ymin + Math.random() * dy;
    }
  }

  start() {
    if (this._rafId != null) return;
    const loop = (t) => {
      this._rafId = requestAnimationFrame(loop);
      this._frame(t);
    };
    this._rafId = requestAnimationFrame(loop);
  }
  stop() {
    if (this._rafId != null) cancelAnimationFrame(this._rafId);
    this._rafId = null;
  }
  dispose() { this.stop(); }

  _frame() {
    if (!this.step || !this.state || !this.accum) return;
    const start = performance.now();
    const [xmin, xmax, ymin, ymax] = this.view;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const sx = w / (xmax - xmin);
    const sy = h / (ymax - ymin);
    const accum = this.accum;
    const state = this.state;
    const step = this.step;
    const p = this.params;
    const N = this._effectiveN * 2;
    const passes = this.iterationsPerFrame;
    const cs = this.colorSpeed;
    const phaseRad = this.colorPhase * Math.PI / 180.0;

    for (let pass = 0; pass < passes; pass++) {
      for (let i = 0; i < N; i += 2) {
        const x = state[i];
        const y = state[i + 1];
        const out = step(x, y, p);
        const nx = out[0];
        const ny = out[1];
        state[i] = nx;
        state[i + 1] = ny;
        const dx = nx - x;
        const dy = ny - y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const t = dist * cs;
        const r = 0.5 + 0.5 * Math.cos(PI2 * t - phaseRad);
        const g = 0.5 + 0.5 * Math.cos(PI2 * (t - 1 / 3) - phaseRad);
        const b = 0.5 + 0.5 * Math.cos(PI2 * (t - 2 / 3) - phaseRad);
        const px = (nx - xmin) * sx;
        const py = (ny - ymin) * sy;
        if (px >= 0 && px < w && py >= 0 && py < h) {
          const idx = ((h - 1 - (py | 0)) * w + (px | 0)) * 4;
          accum[idx + 0] += 1;
          accum[idx + 1] += r;
          accum[idx + 2] += g;
          accum[idx + 3] += b;
        }
      }
      this.totalSamples += this._effectiveN;
    }

    this._tonemap();
    this.ctx.putImageData(this.image, 0, 0);

    const elapsed = performance.now() - start;
    this._lastFrameMs = elapsed;
    if (elapsed > 30 && this._effectiveN > 25_000) {
      this._effectiveN = Math.max(25_000, (this._effectiveN * 0.7) | 0);
    } else if (elapsed < 12 && this._effectiveN < this.n) {
      this._effectiveN = Math.min(this.n, (this._effectiveN * 1.15) | 0);
    }
  }

  _tonemap() {
    const accum = this.accum;
    const data = this.image.data;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const total = this.totalSamples;
    const scale = Math.max(total / (w * h), 1e-6);
    const logScale = Math.log(1000);
    const brightness = 0.3;
    const contrast = 1.0;
    const gamma = 2.2;
    const invGamma = 1.0 / gamma;
    const saturation = 0.8;
    const dynamicRange = 0.2;
    const whiteBg = this.background === "white";
    const usePhase = this.colormap === "phase";
    const lutName = usePhase ? null : this.colormap;

    for (let i = 0, j = 0; i < accum.length; i += 4, j += 4) {
      const count = accum[i];
      let v;
      if (count === 0) v = -20;
      else v = Math.log(count / scale) / logScale;
      let value = contrast * v + brightness;
      value = smoothLimit(value, dynamicRange);
      if (whiteBg) value = 1 - value;

      let r, g, b;
      if (usePhase) {
        let rgbR = 0, rgbG = 0, rgbB = 0;
        if (count > 0) {
          const inv = 1 / count;
          rgbR = accum[i + 1] * inv;
          rgbG = accum[i + 2] * inv;
          rgbB = accum[i + 3] * inv;
        }
        const yuv = rgb2yuv(rgbR, rgbG, rgbB);
        yuv[0] = value;
        const m = saturation * value * (1 - value) * 4;
        yuv[1] *= m;
        yuv[2] *= m;
        const out = yuv2rgb(yuv[0], yuv[1], yuv[2]);
        r = out[0]; g = out[1]; b = out[2];
      } else {
        const c = colormapRGB(lutName, value);
        r = c[0]; g = c[1]; b = c[2];
      }
      const rc = Math.max(0, Math.min(1, r));
      const gc = Math.max(0, Math.min(1, g));
      const bc = Math.max(0, Math.min(1, b));
      data[j + 0] = Math.pow(rc, invGamma) * 255 | 0;
      data[j + 1] = Math.pow(gc, invGamma) * 255 | 0;
      data[j + 2] = Math.pow(bc, invGamma) * 255 | 0;
      data[j + 3] = 255;
    }
  }
}
