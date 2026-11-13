import createREGL from "regl";

const HISTOGRAM_BINS = 24;

// Runs in a Web Worker so the full matrix never blocks the page. It owns the
// data, the "active" rows left after Keep/Exclude filters, and answers
// selection requests with exact counts and histograms plus a bounded sample
// of rows to draw. Backticks can't appear in here: this is a template string.
const WORKER_SOURCE = String.raw`
let matrix = null;
let colors = null;
let rows = 0;
let columns = 0;
let categoryCount = 1;
let histogramBins = 24;
let sampleLimit = 0;
let active = null;
let activeCount = 0;
let extents = null;

// A fixed pseudo-random number per row. Sampling by comparing it to a
// threshold keeps the drawn rows stable while a selection is dragged.
function rowHash(row) {
  let h = Math.imul(row ^ 0x9e3779b9, 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

function pointInPolygon(x, y, vertices) {
  let inside = false;
  for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i, i += 1) {
    const xi = vertices[i][0];
    const yi = vertices[i][1];
    const xj = vertices[j][0];
    const yj = vertices[j][1];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// (row) => bool for a selection dict, in the same format Python syncs.
// Non-finite values fail the bounds check and are never selected.
function selectionTest(selection) {
  const xColumn = selection.x_index;
  const yColumn = selection.y_index;
  let xMin, xMax, yMin, yMax;
  let vertices = null;
  if (selection.type === "box") {
    xMin = selection.x_min; xMax = selection.x_max;
    yMin = selection.y_min; yMax = selection.y_max;
  } else {
    vertices = selection.vertices;
    xMin = Infinity; xMax = -Infinity; yMin = Infinity; yMax = -Infinity;
    for (const [x, y] of vertices) {
      xMin = Math.min(xMin, x); xMax = Math.max(xMax, x);
      yMin = Math.min(yMin, y); yMax = Math.max(yMax, y);
    }
  }
  return (row) => {
    const x = matrix[row * columns + xColumn];
    const y = matrix[row * columns + yColumn];
    if (!(x >= xMin && x <= xMax && y >= yMin && y <= yMax)) return false;
    return vertices === null || pointInPolygon(x, y, vertices);
  };
}

// Replay Keep/Exclude steps from scratch: keep drops rows outside its
// selection, exclude drops rows inside it.
function applyFilters(filters) {
  active = new Uint8Array(rows).fill(1);
  for (const step of filters) {
    const test = selectionTest(step.selection);
    const keep = step.action === "keep";
    for (let row = 0; row < rows; row += 1) {
      if (active[row] && test(row) !== keep) active[row] = 0;
    }
  }
  activeCount = 0;
  for (let row = 0; row < rows; row += 1) activeCount += active[row];
}

// Axis ranges over the active rows, padded a little.
function computeExtents() {
  const result = new Float64Array(columns * 2);
  for (let column = 0; column < columns; column += 1) {
    let low = Infinity;
    let high = -Infinity;
    for (let row = 0; row < rows; row += 1) {
      if (!active[row]) continue;
      const value = matrix[row * columns + column];
      if (!Number.isFinite(value)) continue;
      if (value < low) low = value;
      if (value > high) high = value;
    }
    if (!Number.isFinite(low)) {
      low = -1;
      high = 1;
    } else if (low === high) {
      const padding = Math.abs(low) * 0.05 || 1;
      low -= padding;
      high += padding;
    } else {
      const padding = (high - low) * 0.035;
      low -= padding;
      high += padding;
    }
    result[column * 2] = low;
    result[column * 2 + 1] = high;
  }
  return result;
}

function makeHistograms(mask) {
  const totals = new Uint32Array(columns * histogramBins);
  const byColor = new Uint32Array(columns * histogramBins * categoryCount);
  for (let row = 0; row < rows; row += 1) {
    if (!mask[row]) continue;
    const code = Math.max(0, Math.min(categoryCount - 1, colors[row]));
    for (let column = 0; column < columns; column += 1) {
      const value = matrix[row * columns + column];
      if (!Number.isFinite(value)) continue;
      const low = extents[column * 2];
      const high = extents[column * 2 + 1];
      const bin = Math.max(0, Math.min(histogramBins - 1, Math.floor(((value - low) / (high - low)) * histogramBins)));
      totals[column * histogramBins + bin] += 1;
      byColor[(column * histogramBins + bin) * categoryCount + code] += 1;
    }
  }
  return { totals, byColor };
}

// Every row in the mask when they fit the budget, else ~sampleLimit of them.
function sampleRows(mask, count) {
  const keep = count <= sampleLimit ? 1 : sampleLimit / count;
  const picked = [];
  for (let row = 0; row < rows; row += 1) {
    if (mask[row] && (keep === 1 || rowHash(row) < keep)) picked.push(row);
  }
  const values = new Float32Array(picked.length * columns);
  const codes = new Int32Array(picked.length);
  for (let i = 0; i < picked.length; i += 1) {
    const row = picked[i];
    values.set(matrix.subarray(row * columns, (row + 1) * columns), i * columns);
    codes[i] = colors[row];
  }
  return { values, codes };
}

function summary(mask, count) {
  const histograms = makeHistograms(mask);
  const sample = sampleRows(mask, count);
  const message = {
    sampleCount: sample.codes.length,
    histogramTotals: histograms.totals.buffer,
    histogramByColor: histograms.byColor.buffer,
    sampleValues: sample.values.buffer,
    sampleColors: sample.codes.buffer,
  };
  const transfer = [message.histogramTotals, message.histogramByColor, message.sampleValues, message.sampleColors];
  return { message, transfer };
}

function postView(version) {
  extents = computeExtents();
  const { message, transfer } = summary(active, activeCount);
  // Send a copy: the worker keeps using its own extents.
  const extentsCopy = extents.slice();
  postMessage(
    { type: "view", version, rows, columns, activeCount, extents: extentsCopy.buffer, ...message },
    [extentsCopy.buffer, ...transfer]
  );
}

function handleSelect(data) {
  const test = selectionTest(data.selection);
  const selected = new Uint8Array(rows);
  let count = 0;
  for (let row = 0; row < rows; row += 1) {
    if (active[row] && test(row)) {
      selected[row] = 1;
      count += 1;
    }
  }
  const { message, transfer } = summary(selected, count);
  postMessage({ type: "selected", requestId: data.requestId, count, ...message }, transfer);
}

self.onmessage = (event) => {
  const data = event.data;
  try {
    if (data.type === "load") {
      rows = data.rows;
      columns = data.columns;
      categoryCount = Math.max(1, data.categoryCount);
      histogramBins = data.histogramBins;
      sampleLimit = data.sampleLimit;
      matrix = new Float32Array(data.matrixBuffer);
      colors = new Int32Array(data.colorBuffer);
      applyFilters(data.filters);
      postView(data.version);
    } else if (data.type === "filters") {
      applyFilters(data.filters);
      postView(data.version);
    } else if (data.type === "select") {
      handleSelect(data);
    }
  } catch (error) {
    postMessage({ type: "error", message: error && error.stack ? error.stack : String(error) });
  }
};
`;

// Always copy: the same message buffers can be shared by several views of one
// model, so transferring the original would detach it for the other views.
function copyBuffer(view) {
  return view.buffer.slice(view.byteOffset, view.byteOffset + view.byteLength);
}

// marimo renders widgets inside a shadow root, so CSS ancestor selectors can't
// see the notebook theme. Walk up through shadow hosts and look for it.
function resolveDark(el) {
  for (let n = el; n; n = n.parentNode || n.host) {
    if (n.nodeType !== 1) continue;
    const cls = n.classList;
    const mode = n.getAttribute("data-theme") || n.getAttribute("data-color-mode");
    const jpLight = n.getAttribute("data-jp-theme-light");
    if (cls.contains("dark") || cls.contains("dark-theme") || mode === "dark" || jpLight === "false") return true;
    if (cls.contains("light") || cls.contains("light-theme") || mode === "light" || jpLight === "true") return false;
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

// Dark-surface steps for the default palette (same hues, re-stepped so they
// keep 3:1 contrast on a dark background). Custom colors are used as given.
const DARK_STEPS = {
  "#2a78d6": "#3987e5",
  "#eb6834": "#d95926",
  "#1baf7a": "#199e70",
  "#eda100": "#c98500",
  "#e87ba4": "#d55181",
  "#008300": "#008300",
  "#6250d6": "#9085e9",
  "#e34948": "#e66767",
};

const ANIMATION_MS = 550;

function ease(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
}

const FONT = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const GAP = 6;

function parseColor(color) {
  const probe = document.createElement("canvas").getContext("2d");
  probe.fillStyle = "#000000";
  probe.fillStyle = color;
  const value = probe.fillStyle;
  if (value.startsWith("#")) {
    return [1, 3, 5].map((offset) => parseInt(value.slice(offset, offset + 2), 16) / 255).concat(1);
  }
  const numbers = (value.match(/[\d.]+/g) || [0, 0, 0, 1]).map(Number);
  return [numbers[0] / 255, numbers[1] / 255, numbers[2] / 255, numbers.length > 3 ? numbers[3] : 1];
}

function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

// About `count` round-numbered ticks inside [low, high].
function niceTicks(low, high, count) {
  const span = high - low;
  if (!(span > 0)) return { ticks: [], step: 1 };
  const raw = span / count;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const norm = raw / magnitude;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * magnitude;
  const ticks = [];
  for (let value = Math.ceil(low / step) * step; value <= high + step * 1e-9; value += step) {
    ticks.push(Math.abs(value) < step * 1e-9 ? 0 : value);
  }
  return { ticks, step };
}

const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });

function formatTick(value, step) {
  if (Math.abs(value) >= 10000) return compact.format(value);
  const decimals = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
  return value.toFixed(decimals);
}

function insidePath(point, path) {
  let inside = false;
  for (let i = 0, j = path.length - 1; i < path.length; j = i, i += 1) {
    const a = path[i];
    const b = path[j];
    if ((a.y > point.y) !== (b.y > point.y) && point.x < ((b.x - a.x) * (point.y - a.y)) / (b.y - a.y) + a.x) {
      inside = !inside;
    }
  }
  return inside;
}

function simplify(points, tolerance = 2.5) {
  if (points.length <= 3) return points;
  const result = [points[0]];
  let previous = points[0];
  for (let i = 1; i < points.length; i += 1) {
    const dx = points[i].x - previous.x;
    const dy = points[i].y - previous.y;
    if (dx * dx + dy * dy > tolerance * tolerance) {
      result.push(points[i]);
      previous = points[i];
    }
  }
  return result;
}

function render({ model, el }) {
  el.classList.add("pair-plot-root");
  const root = document.createElement("div");
  root.className = "pp-shell";
  root.innerHTML = `
    <div class="pp-bar">
      <div class="pp-legend"></div>
      <div class="pp-controls">
        <span class="pp-status">Loading…</span>
        <div class="pp-group" role="group" aria-label="Selection actions">
          <button type="button" data-action="keep" title="Keep only the selected rows">Keep</button>
          <button type="button" data-action="exclude" title="Drop the selected rows">Exclude</button>
          <button type="button" data-action="clear" title="Clear the selection">Clear</button>
        </div>
        <button type="button" class="pp-button" data-action="reset" title="Bring back every row">Reset</button>
        <div class="pp-segmented" role="group" aria-label="Selection tool">
          <button type="button" data-mode="box">Box</button>
          <button type="button" data-mode="lasso">Lasso</button>
        </div>
        <div class="pp-segmented" role="group" aria-label="Layout">
          <button type="button" data-layout="full">Full</button>
          <button type="button" data-layout="lower">Lower</button>
        </div>
      </div>
    </div>
    <div class="pp-scroll"><div class="pp-stage">
      <canvas class="pp-gl"></canvas>
      <canvas class="pp-overlay"></canvas>
    </div></div>
    <pre class="pp-error" hidden></pre>
  `;
  el.appendChild(root);

  const glCanvas = root.querySelector(".pp-gl");
  const overlay = root.querySelector(".pp-overlay");
  const ctx = overlay.getContext("2d");
  const stage = root.querySelector(".pp-stage");
  const statusEl = root.querySelector(".pp-status");
  const legend = root.querySelector(".pp-legend");
  const errorBox = root.querySelector(".pp-error");
  const layoutButtons = [...root.querySelectorAll("[data-layout]")];
  const modeButtons = [...root.querySelectorAll("[data-mode]")];
  const keepButton = root.querySelector("[data-action='keep']");
  const excludeButton = root.querySelector("[data-action='exclude']");
  const clearButton = root.querySelector("[data-action='clear']");
  const resetButton = root.querySelector("[data-action='reset']");
  const actionGroup = root.querySelector("[aria-label='Selection actions']");
  const modeGroup = root.querySelector("[aria-label='Selection tool']");
  const layoutGroup = root.querySelector("[aria-label='Layout']");

  // Which toolbar buttons show is up to Python. Without the filter buttons,
  // clicking empty space or double-clicking still clears the selection.
  function renderToolbar() {
    const filtering = model.get("show_filters");
    actionGroup.hidden = !filtering;
    resetButton.hidden = !filtering;
    modeGroup.hidden = !model.get("show_mode_toggle");
    layoutGroup.hidden = !model.get("show_layout_toggle");
  }
  renderToolbar();

  function showError(message) {
    errorBox.hidden = false;
    errorBox.textContent = message;
    model.set("error", message);
    model.set("status", "error");
    model.save_changes();
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
    if (model.get("error")) {
      model.set("error", "");
      model.save_changes();
    }
  }

  let regl;
  try {
    regl = createREGL({ canvas: glCanvas, attributes: { alpha: true, antialias: true, premultipliedAlpha: false } });
  } catch (error) {
    showError(`WebGL could not start: ${error.message || error}`);
    return;
  }

  const workerUrl = URL.createObjectURL(new Blob([WORKER_SOURCE], { type: "text/javascript" }));
  const worker = new Worker(workerUrl);
  const state = {
    rows: 0,
    columns: 0,
    activeCount: 0, // rows left after Keep/Exclude filters
    filtersKey: null, // JSON of the filters last sent to the worker
    filtering: false,
    sampleCount: 0,
    extents: null,
    histogramTotals: null,
    histogramByColor: null,
    sampleColors: null,
    selectedCount: 0,
    selectedSampleCount: 0,
    selectedHistogramByColor: null,
    selectedColors: null,
    baseMatrixBuffer: null,
    baseColorBuffer: null,
    selectedMatrixBuffer: null,
    selectedColorBuffer: null,
    // Selection requests: at most one is in the worker at a time; while a box
    // is dragged, the newest pending one waits in `queued` and older ones are
    // dropped. Results with requestId <= ignoreUpTo (sent before a clear or a
    // data reload) are discarded.
    requestCounter: 0,
    inFlight: false,
    queued: null,
    ignoreUpTo: 0,
    appliedKey: null,
    live: null, // the selection being drawn or moved, before it is committed
    drag: null,
    hover: null,
    // While Keep/Exclude/Reset animates: the axis ranges glide from `from` to
    // the new extents, and `ghost` (the previous point sample) fades out.
    anim: null,
    dark: null,
  };

  // ---- geometry -------------------------------------------------------------

  function geometry() {
    const n = state.columns;
    const left = 40;
    const top = 2;
    const right = 2;
    const bottom = 20;
    const fixed = model.get("cell_size");
    const available = Math.max(320, root.clientWidth || 900);
    const fit = Math.floor((available - left - right - GAP * (n - 1)) / n);
    const cell = fixed || clamp(fit, 56, 200);
    const matrix = n * cell + (n - 1) * GAP;
    return { n, left, top, right, bottom, cell, matrix, width: left + matrix + right, height: top + matrix + bottom };
  }

  function cellBox(g, row, column) {
    return { x: g.left + column * (g.cell + GAP), y: g.top + row * (g.cell + GAP), size: g.cell };
  }

  function isVisible(row, column) {
    return model.get("layout") === "full" || row >= column;
  }

  function currentSelection() {
    return state.live || model.get("selection") || {};
  }

  function hasSelection() {
    const type = currentSelection().type;
    return type === "box" || type === "lasso";
  }

  // True once the worker has answered for some selection; until then the
  // matrix keeps showing the unselected view. While a Keep/Exclude is being
  // computed the last selection stays on screen, so nothing flashes before
  // the new view (and its animation) arrives.
  function showsSelection() {
    return (hasSelection() || state.filtering) && state.selectedHistogramByColor !== null;
  }

  function animationProgress() {
    return state.anim ? ease(state.anim.progress) : 1;
  }

  // Axis ranges as drawn. Equal to the worker's extents except mid-animation.
  function shownExtents() {
    const anim = state.anim;
    if (!anim) return state.extents;
    const k = animationProgress();
    return state.extents.map((value, i) => anim.from[i] + (value - anim.from[i]) * k);
  }

  function stopAnimation() {
    const anim = state.anim;
    if (!anim) return;
    cancelAnimationFrame(anim.frame);
    anim.ghost.matrix.destroy();
    anim.ghost.colors.destroy();
    state.anim = null;
  }

  function startAnimation(from, fromTotals, ghost) {
    state.anim = { from, fromTotals, ghost, start: performance.now(), progress: 0, frame: 0 };
    const step = (now) => {
      const anim = state.anim;
      if (!anim) return;
      anim.progress = Math.min(1, (now - anim.start) / ANIMATION_MS);
      if (anim.progress < 1) {
        const t = theme();
        renderPoints(t);
        renderOverlay(t);
        anim.frame = requestAnimationFrame(step);
      } else {
        stopAnimation();
        renderAll();
      }
    };
    state.anim.frame = requestAnimationFrame(step);
  }

  function resizeCanvases() {
    if (!state.columns) return;
    const g = geometry();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    stage.style.width = `${g.width}px`;
    stage.style.height = `${g.height}px`;
    for (const canvas of [glCanvas, overlay]) {
      canvas.style.width = `${g.width}px`;
      canvas.style.height = `${g.height}px`;
      canvas.width = Math.round(g.width * ratio);
      canvas.height = Math.round(g.height * ratio);
    }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    regl.poll();
  }

  // ---- theme & colors -------------------------------------------------------

  function theme() {
    const dark = resolveDark(el);
    el.classList.toggle("pair-plot--dark", dark);
    const style = getComputedStyle(root);
    const read = (name) => style.getPropertyValue(name).trim();
    return {
      dark,
      ink: read("--pp-ink"),
      muted: read("--pp-muted"),
      hair: read("--pp-hair"),
      panel: read("--pp-panel"),
      context: read("--pp-context"),
      lasso: read("--pp-lasso"),
      lassoFill: read("--pp-lasso-fill"),
    };
  }

  function palette(dark) {
    const colors = model.get("palette") || [];
    const list = colors.length ? colors : ["#2a78d6"];
    return list.map((color) => (dark && DARK_STEPS[color.toLowerCase()]) || color);
  }

  function colorArray(codes, dark) {
    const rgb = palette(dark).map(parseColor);
    const values = new Float32Array(codes.length * 3);
    for (let i = 0; i < codes.length; i += 1) {
      values.set(rgb[clamp(codes[i], 0, rgb.length - 1)].slice(0, 3), i * 3);
    }
    return values;
  }

  function replaceBuffer(name, values) {
    if (state[name]) state[name].destroy();
    state[name] = regl.buffer(values);
  }

  function rebuildColorBuffers(dark) {
    if (state.sampleColors) replaceBuffer("baseColorBuffer", colorArray(state.sampleColors, dark));
    if (state.selectedColors) replaceBuffer("selectedColorBuffer", colorArray(state.selectedColors, dark));
    state.dark = dark;
  }

  // ---- WebGL: cell panels and points ----------------------------------------

  const drawPanel = regl({
    vert: "attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }",
    frag: "precision mediump float; uniform vec4 color; void main() { gl_FragColor = color; }",
    attributes: { p: [[-1, -1], [3, -1], [-1, 3]] },
    uniforms: { color: regl.prop("color") },
    viewport: regl.prop("viewport"),
    scissor: { enable: true, box: regl.prop("viewport") },
    count: 3,
    depth: { enable: false },
  });

  const drawPoints = regl({
    vert: `
      precision highp float;
      attribute float xValue;
      attribute float yValue;
      attribute vec3 pointColor;
      uniform vec2 xDomain;
      uniform vec2 yDomain;
      uniform float pointSize;
      uniform float useContext;
      uniform vec3 contextColor;
      varying vec3 color;
      void main() {
        bool invalid = xValue != xValue || yValue != yValue || abs(xValue) > 1.0e30 || abs(yValue) > 1.0e30;
        vec2 position = vec2(
          (xValue - xDomain.x) / (xDomain.y - xDomain.x) * 2.0 - 1.0,
          (yValue - yDomain.x) / (yDomain.y - yDomain.x) * 2.0 - 1.0
        );
        gl_Position = invalid ? vec4(2.0, 2.0, 0.0, 1.0) : vec4(position, 0.0, 1.0);
        gl_PointSize = pointSize;
        color = mix(pointColor, contextColor, useContext);
      }
    `,
    frag: `
      precision mediump float;
      uniform float opacity;
      varying vec3 color;
      void main() {
        vec2 centered = gl_PointCoord - vec2(0.5);
        float edge = length(centered);
        if (edge > 0.5) discard;
        gl_FragColor = vec4(color, opacity * smoothstep(0.5, 0.36, edge));
      }
    `,
    attributes: {
      xValue: regl.prop("xAttribute"),
      yValue: regl.prop("yAttribute"),
      pointColor: regl.prop("colorAttribute"),
    },
    uniforms: {
      xDomain: regl.prop("xDomain"),
      yDomain: regl.prop("yDomain"),
      pointSize: regl.prop("pointSize"),
      opacity: regl.prop("opacity"),
      useContext: regl.prop("useContext"),
      contextColor: regl.prop("contextColor"),
    },
    viewport: regl.prop("viewport"),
    scissor: { enable: true, box: regl.prop("viewport") },
    primitive: "points",
    count: regl.prop("count"),
    depth: { enable: false },
    blend: {
      enable: true,
      func: { srcRGB: "src alpha", srcAlpha: 1, dstRGB: "one minus src alpha", dstAlpha: "one minus src alpha" },
    },
  });

  // Point size and opacity follow how crowded a cell is: big, solid dots for
  // a few hundred rows, small translucent ones once the sample is dense, so
  // overlap reads as density instead of a solid blob.
  function pointStyle(count, g) {
    const area = g.cell * g.cell;
    const size = model.get("point_size") || clamp(Math.sqrt(area / Math.max(1, count)) * 0.8, 1.6, 5);
    const dot = Math.PI * (size / 2) ** 2;
    const opacity = clamp((1.6 * area) / (Math.max(1, count) * dot), 0.06, 0.85);
    return { size, opacity };
  }

  function renderPoints(t) {
    regl.poll();
    regl.clear({ color: [0, 0, 0, 0], depth: 1 });
    if (!state.baseMatrixBuffer || !state.extents) return;
    const g = geometry();
    const ratio = glCanvas.width / g.width;
    const stride = state.columns * 4;
    const selected = showsSelection();
    const panel = parseColor(t.panel);
    const context = parseColor(t.context).slice(0, 3);
    const base = pointStyle(state.sampleCount, g);
    const picked = pointStyle(state.selectedSampleCount, g);
    const extents = shownExtents();
    const ghost = state.anim ? state.anim.ghost : null;
    const ghostStyle = ghost ? pointStyle(ghost.count, g) : null;
    const fade = 1 - animationProgress();
    for (let row = 0; row < state.columns; row += 1) {
      for (let column = 0; column < state.columns; column += 1) {
        if (!isVisible(row, column)) continue;
        const box = cellBox(g, row, column);
        const viewport = {
          x: Math.round(box.x * ratio),
          y: Math.round((g.height - box.y - box.size) * ratio),
          width: Math.round(box.size * ratio),
          height: Math.round(box.size * ratio),
        };
        drawPanel({ viewport, color: panel });
        if (row === column) continue;
        const common = {
          viewport,
          xDomain: [extents[column * 2], extents[column * 2 + 1]],
          yDomain: [extents[row * 2], extents[row * 2 + 1]],
          contextColor: context,
        };
        if (ghost) {
          drawPoints({
            ...common,
            xAttribute: { buffer: ghost.matrix, stride, offset: column * 4 },
            yAttribute: { buffer: ghost.matrix, stride, offset: row * 4 },
            colorAttribute: { buffer: ghost.colors, stride: 12, offset: 0 },
            count: ghost.count,
            pointSize: ghostStyle.size * ratio,
            opacity: ghostStyle.opacity * fade,
            useContext: 1,
          });
        }
        drawPoints({
          ...common,
          xAttribute: { buffer: state.baseMatrixBuffer, stride, offset: column * 4 },
          yAttribute: { buffer: state.baseMatrixBuffer, stride, offset: row * 4 },
          colorAttribute: { buffer: state.baseColorBuffer, stride: 12, offset: 0 },
          count: state.sampleCount,
          pointSize: base.size * ratio,
          opacity: selected ? Math.min(0.5, base.opacity) : base.opacity,
          useContext: selected ? 1 : 0,
        });
        if (selected && state.selectedSampleCount) {
          drawPoints({
            ...common,
            xAttribute: { buffer: state.selectedMatrixBuffer, stride, offset: column * 4 },
            yAttribute: { buffer: state.selectedMatrixBuffer, stride, offset: row * 4 },
            colorAttribute: { buffer: state.selectedColorBuffer, stride: 12, offset: 0 },
            count: state.selectedSampleCount,
            pointSize: picked.size * ratio,
            opacity: picked.opacity,
            useContext: 0,
          });
        }
      }
    }
  }

  // ---- 2D overlay: histograms, ticks, labels, lasso -------------------------

  function drawHistogram(column, box, t, colors) {
    const selected = showsSelection();
    const baseTotals = state.histogramTotals;
    const byColor = selected ? state.selectedHistogramByColor : state.histogramByColor;
    if (!baseTotals || !byColor) return;
    const categories = colors.length;
    const offset = column * HISTOGRAM_BINS;
    const peak = (totals) => {
      let maximum = 1;
      for (let bin = 0; bin < HISTOGRAM_BINS; bin += 1) maximum = Math.max(maximum, totals[offset + bin]);
      return maximum;
    };
    let maximum = peak(baseTotals);

    // Bins are computed over the current extents; place them through the
    // shown (possibly animating) range so they stretch along with the axes.
    const extents = shownExtents();
    const shownLow = extents[column * 2];
    const shownHigh = extents[column * 2 + 1];
    const toX = (value) => box.x + 4 + ((value - shownLow) / (shownHigh - shownLow)) * (box.size - 8);
    const left = toX(state.extents[column * 2]);
    const binWidth = (toX(state.extents[column * 2 + 1]) - left) / HISTOGRAM_BINS;
    const barWidth = binWidth > 3 ? binWidth - 1 : binWidth;
    if (state.anim) {
      const from = peak(state.anim.fromTotals);
      maximum = from + (maximum - from) * animationProgress();
    }

    const labelHeight = box.size < 80 ? 18 : 24;
    const baseline = box.y + box.size - 4;
    const height = box.size - labelHeight - 6;
    ctx.save();
    ctx.beginPath();
    ctx.rect(box.x, box.y, box.size, box.size);
    ctx.clip();

    if (selected) {
      ctx.fillStyle = t.context;
      ctx.globalAlpha = 0.55;
      for (let bin = 0; bin < HISTOGRAM_BINS; bin += 1) {
        const h = (height * baseTotals[offset + bin]) / maximum;
        if (h > 0) ctx.fillRect(left + bin * binWidth, baseline - h, barWidth, h);
      }
      ctx.globalAlpha = 1;
    }
    for (let bin = 0; bin < HISTOGRAM_BINS; bin += 1) {
      let bottom = baseline;
      for (let category = 0; category < categories; category += 1) {
        const h = (height * byColor[(offset + bin) * categories + category]) / maximum;
        if (!h) continue;
        ctx.fillStyle = colors[category];
        ctx.fillRect(left + bin * binWidth, bottom - h, barWidth, h);
        bottom -= h;
      }
    }
    ctx.restore();
  }

  function drawTicks(g, t) {
    const n = state.columns;
    const extents = shownExtents();
    const count = g.cell >= 140 ? 4 : g.cell >= 80 ? 3 : 2;
    ctx.font = `10px ${FONT}`;
    ctx.fillStyle = t.muted;
    ctx.strokeStyle = t.hair;
    ctx.lineWidth = 1;

    // x ticks under the bottom row, one set per column.
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let column = 0; column < n; column += 1) {
      const box = cellBox(g, n - 1, column);
      const low = extents[column * 2];
      const high = extents[column * 2 + 1];
      const { ticks, step } = niceTicks(low, high, count);
      for (const value of ticks) {
        const x = box.x + ((value - low) / (high - low)) * box.size;
        const label = formatTick(value, step);
        const half = ctx.measureText(label).width / 2;
        if (x - half < box.x - GAP / 2 || x + half > box.x + box.size + GAP / 2) continue;
        ctx.beginPath();
        ctx.moveTo(Math.round(x) + 0.5, box.y + box.size);
        ctx.lineTo(Math.round(x) + 0.5, box.y + box.size + 3);
        ctx.stroke();
        ctx.fillText(label, x, box.y + box.size + 5);
      }
    }

    // y ticks left of the first column. In the lower layout row 0 only holds
    // the histogram, whose height is a count, so it gets none.
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    const firstRow = model.get("layout") === "lower" ? 1 : 0;
    for (let row = firstRow; row < n; row += 1) {
      const box = cellBox(g, row, 0);
      const low = extents[row * 2];
      const high = extents[row * 2 + 1];
      const { ticks, step } = niceTicks(low, high, count);
      for (const value of ticks) {
        const y = box.y + (1 - (value - low) / (high - low)) * box.size;
        if (y - 6 < box.y - GAP / 2 || y + 6 > box.y + box.size + GAP / 2) continue;
        ctx.beginPath();
        ctx.moveTo(box.x - 3, Math.round(y) + 0.5);
        ctx.lineTo(box.x, Math.round(y) + 0.5);
        ctx.stroke();
        ctx.fillText(formatTick(value, step), box.x - 5, y, g.left - 8);
      }
    }
  }

  // Data coordinates -> overlay pixels for the cell a selection lives in.
  function selectionToPixels(selection, g) {
    if (!state.extents || (selection.type !== "box" && selection.type !== "lasso")) return null;
    const box = cellBox(g, selection.y_index, selection.x_index);
    const xLow = state.extents[selection.x_index * 2];
    const xHigh = state.extents[selection.x_index * 2 + 1];
    const yLow = state.extents[selection.y_index * 2];
    const yHigh = state.extents[selection.y_index * 2 + 1];
    const vertices =
      selection.type === "box"
        ? [
            [selection.x_min, selection.y_min],
            [selection.x_max, selection.y_min],
            [selection.x_max, selection.y_max],
            [selection.x_min, selection.y_max],
          ]
        : selection.vertices;
    return vertices.map(([x, y]) => ({
      x: box.x + ((x - xLow) / (xHigh - xLow)) * box.size,
      y: box.y + (1 - (y - yLow) / (yHigh - yLow)) * box.size,
    }));
  }

  function renderOverlay(t) {
    if (!state.columns) return;
    const g = geometry();
    const names = model.get("columns") || [];
    const colors = palette(t.dark);
    ctx.clearRect(0, 0, g.width, g.height);

    for (let i = 0; i < state.columns; i += 1) {
      const box = cellBox(g, i, i);
      drawHistogram(i, box, t, colors);
      ctx.font = `600 ${box.size < 80 ? 10 : 11}px ${FONT}`;
      ctx.fillStyle = t.ink;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(names[i] || `x${i}`, box.x + 6, box.y + 6, box.size - 12);
    }
    drawTicks(g, t);

    if (state.hover && !state.drag) {
      const box = cellBox(g, state.hover.row, state.hover.column);
      ctx.strokeStyle = t.hair;
      ctx.lineWidth = 1;
      ctx.strokeRect(box.x + 0.5, box.y + 0.5, box.size - 1, box.size - 1);
    }

    const path = state.drag && state.drag.kind === "lasso" ? state.drag.points : selectionToPixels(currentSelection(), g);
    if (path && path.length > 1) {
      ctx.beginPath();
      ctx.moveTo(path[0].x, path[0].y);
      for (let i = 1; i < path.length; i += 1) ctx.lineTo(path[i].x, path[i].y);
      ctx.closePath();
      ctx.fillStyle = t.lassoFill;
      ctx.fill();
      ctx.strokeStyle = t.lasso;
      ctx.lineWidth = 1.5;
      ctx.lineJoin = "round";
      ctx.stroke();
    }
  }

  // ---- DOM chrome -----------------------------------------------------------

  function renderLegend(t) {
    const categories = model.get("categories") || [];
    const colors = palette(t.dark);
    legend.replaceChildren(
      ...categories.map((category, index) => {
        const item = document.createElement("span");
        item.className = "pp-key";
        const swatch = document.createElement("i");
        swatch.style.background = colors[index];
        item.append(swatch, category);
        return item;
      })
    );
  }

  function percent(part, whole) {
    const share = whole ? (100 * part) / whole : 0;
    return share < 10 ? share.toFixed(1) : String(Math.round(share));
  }

  function renderStatus() {
    const names = model.get("columns") || [];
    const filters = model.get("filters") || [];
    const shown = state.activeCount.toLocaleString();
    statusEl.replaceChildren();
    if (!state.columns) {
      statusEl.textContent = "Loading…";
    } else if (state.filtering) {
      statusEl.textContent = "Filtering…";
    } else if (hasSelection() && !showsSelection()) {
      statusEl.textContent = "Selecting…";
    } else if (hasSelection()) {
      const strong = document.createElement("strong");
      strong.textContent = state.selectedCount.toLocaleString();
      statusEl.append(strong, ` of ${shown} rows · ${percent(state.selectedCount, state.activeCount)}%`);
    } else if (filters.length) {
      const steps = filters.length === 1 ? "1 filter" : `${filters.length} filters`;
      statusEl.textContent = `${shown} of ${state.rows.toLocaleString()} rows · ${steps}`;
    } else if (state.hover) {
      const verb = model.get("mode") === "box" ? "drag a box" : "drag to lasso";
      statusEl.textContent = `${names[state.hover.column]} × ${names[state.hover.row]} · ${verb}`;
    } else {
      const verb = model.get("mode") === "box" ? "drag a box in any cell" : "lasso in any cell";
      statusEl.textContent = `${shown} rows · ${verb}`;
    }
    const selecting = hasSelection();
    keepButton.disabled = !selecting;
    excludeButton.disabled = !selecting;
    clearButton.disabled = !selecting;
    resetButton.disabled = filters.length === 0;
    layoutButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.layout === model.get("layout"))));
    modeButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.mode === model.get("mode"))));
  }

  function renderAll() {
    watchTheme();
    const t = theme();
    if (state.dark !== t.dark) rebuildColorBuffers(t.dark);
    renderPoints(t);
    renderOverlay(t);
    renderLegend(t);
    renderStatus();
  }

  // ---- selection ------------------------------------------------------------

  function requestSelection(selection) {
    if (state.inFlight) {
      state.queued = selection;
      return;
    }
    state.inFlight = true;
    state.requestCounter += 1;
    worker.postMessage({ type: "select", requestId: state.requestCounter, selection });
  }

  function forgetResult() {
    state.ignoreUpTo = state.requestCounter;
    state.queued = null;
    state.selectedCount = 0;
    state.selectedSampleCount = 0;
    state.selectedHistogramByColor = null;
    state.selectedColors = null;
  }

  // Evaluate `selection` against every row in the worker; renders when the
  // answer comes back. Repeats of the selection already applied are no-ops,
  // which covers the change:selection echo after we set it ourselves.
  function applySelection(selection) {
    const key = JSON.stringify(selection || {});
    if (key === state.appliedKey) return;
    state.appliedKey = key;
    if (!selection || !selection.type || !state.extents) {
      forgetResult();
      renderAll();
      return;
    }
    requestSelection(selection);
    renderOverlay(theme());
    renderStatus();
  }

  // A selection still being drawn or dragged: shown and evaluated live, but
  // only sent to Python on release.
  function previewSelection(selection) {
    state.live = selection;
    applySelection(selection);
  }

  function commitSelection(selection) {
    state.live = null;
    model.set("selection", selection);
    if (!selection.type) model.set("selected_count", 0);
    model.save_changes();
    applySelection(selection);
  }

  // ---- Keep / Exclude / Reset ------------------------------------------------

  // Send the filter list to the worker, which rebuilds the active rows, axes
  // and histograms and answers with a fresh "view".
  function sendFilters() {
    const filters = model.get("filters") || [];
    const key = JSON.stringify(filters);
    if (key === state.filtersKey || !state.columns) return;
    state.filtersKey = key;
    state.filtering = true;
    // Drop answers still on their way, but keep showing the current one.
    state.ignoreUpTo = state.requestCounter;
    state.queued = null;
    worker.postMessage({ type: "filters", filters });
    renderStatus();
  }

  // The selection is cleared with every filter change: the axes rescale to
  // the remaining rows, so the old outline would no longer mean the same.
  function setFilters(filters) {
    state.live = null;
    state.appliedKey = JSON.stringify({});
    model.set("filters", filters);
    model.set("selection", {});
    model.set("selected_count", 0);
    model.save_changes();
    sendFilters();
  }

  function addFilter(action) {
    if (!hasSelection()) return;
    setFilters([...(model.get("filters") || []), { action, selection: currentSelection() }]);
  }

  // ---- pointer interaction --------------------------------------------------

  function pointerPosition(event) {
    const bounds = overlay.getBoundingClientRect();
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  }

  function cellAt(point) {
    const g = geometry();
    const column = Math.floor((point.x - g.left) / (g.cell + GAP));
    const row = Math.floor((point.y - g.top) / (g.cell + GAP));
    if (row < 0 || column < 0 || row >= state.columns || column >= state.columns) return null;
    if (row === column || !isVisible(row, column)) return null;
    const box = cellBox(g, row, column);
    if (point.x > box.x + box.size || point.y > box.y + box.size) return null;
    return { row, column, box };
  }

  function clampToCell(point, cell) {
    return {
      x: clamp(point.x, cell.box.x, cell.box.x + cell.box.size),
      y: clamp(point.y, cell.box.y, cell.box.y + cell.box.size),
    };
  }

  function cellDomain(cell) {
    return {
      xLow: state.extents[cell.column * 2],
      xHigh: state.extents[cell.column * 2 + 1],
      yLow: state.extents[cell.row * 2],
      yHigh: state.extents[cell.row * 2 + 1],
    };
  }

  function pixelToData(point, cell) {
    const { xLow, xHigh, yLow, yHigh } = cellDomain(cell);
    return [
      xLow + ((point.x - cell.box.x) / cell.box.size) * (xHigh - xLow),
      yHigh - ((point.y - cell.box.y) / cell.box.size) * (yHigh - yLow),
    ];
  }

  function boxFromPixels(a, b, cell) {
    const [x1, y1] = pixelToData(a, cell);
    const [x2, y2] = pixelToData(b, cell);
    return {
      type: "box",
      x_index: cell.column,
      y_index: cell.row,
      x_min: Math.min(x1, x2),
      x_max: Math.max(x1, x2),
      y_min: Math.min(y1, y2),
      y_max: Math.max(y1, y2),
    };
  }

  function selectionBounds(selection) {
    if (selection.type === "box") {
      return { xMin: selection.x_min, xMax: selection.x_max, yMin: selection.y_min, yMax: selection.y_max };
    }
    const xs = selection.vertices.map((vertex) => vertex[0]);
    const ys = selection.vertices.map((vertex) => vertex[1]);
    return { xMin: Math.min(...xs), xMax: Math.max(...xs), yMin: Math.min(...ys), yMax: Math.max(...ys) };
  }

  // Shift a box or lasso by a pixel offset, keeping it inside its cell.
  function movedSelection(origin, dx, dy, cell) {
    const { xLow, xHigh, yLow, yHigh } = cellDomain(cell);
    const bounds = selectionBounds(origin);
    const shiftX = clamp((dx / cell.box.size) * (xHigh - xLow), xLow - bounds.xMin, xHigh - bounds.xMax);
    const shiftY = clamp((-dy / cell.box.size) * (yHigh - yLow), yLow - bounds.yMin, yHigh - bounds.yMax);
    if (origin.type === "box") {
      return {
        ...origin,
        x_min: origin.x_min + shiftX,
        x_max: origin.x_max + shiftX,
        y_min: origin.y_min + shiftY,
        y_max: origin.y_max + shiftY,
      };
    }
    return { ...origin, vertices: origin.vertices.map(([x, y]) => [x + shiftX, y + shiftY]) };
  }

  function isInsideSelection(point, cell) {
    const selection = currentSelection();
    if (!hasSelection() || selection.x_index !== cell.column || selection.y_index !== cell.row) return false;
    return insidePath(point, selectionToPixels(selection, geometry()));
  }

  function lassoFromPixels(points, cell) {
    const vertices = simplify(points).map((point) => pixelToData(point, cell));
    return { type: "lasso", x_index: cell.column, y_index: cell.row, vertices };
  }

  overlay.addEventListener("pointerdown", (event) => {
    if (!state.extents || state.anim || event.button !== 0) return;
    const point = pointerPosition(event);
    const cell = cellAt(point);
    if (!cell) return;
    overlay.setPointerCapture(event.pointerId);
    const start = clampToCell(point, cell);
    // Grabbing an existing box or lasso moves it, whichever tool is active.
    if (isInsideSelection(point, cell)) {
      state.drag = { kind: "move", cell, start: point, origin: currentSelection(), moved: false };
    } else if (model.get("mode") === "lasso") {
      state.drag = { kind: "lasso", cell, points: [start], moved: false };
    } else {
      state.drag = { kind: "box", cell, start, moved: false };
    }
    renderOverlay(theme());
  });

  overlay.addEventListener("pointermove", (event) => {
    const point = pointerPosition(event);
    const drag = state.drag;
    if (!drag) {
      const cell = state.extents ? cellAt(point) : null;
      const inside = Boolean(cell && isInsideSelection(point, cell));
      overlay.style.cursor = inside ? "move" : "crosshair";
      const hover = cell ? { row: cell.row, column: cell.column } : null;
      if (JSON.stringify(hover) !== JSON.stringify(state.hover)) {
        state.hover = hover;
        renderOverlay(theme());
        renderStatus();
      }
      return;
    }
    if (drag.kind === "lasso") {
      const next = clampToCell(point, drag.cell);
      const previous = drag.points[drag.points.length - 1];
      if ((next.x - previous.x) ** 2 + (next.y - previous.y) ** 2 >= 9) {
        drag.points.push(next);
        drag.moved = true;
        renderOverlay(theme());
      }
      return;
    }
    const dx = point.x - drag.start.x;
    const dy = point.y - drag.start.y;
    if (!drag.moved && dx * dx + dy * dy < 9) return;
    drag.moved = true;
    if (drag.kind === "box") previewSelection(boxFromPixels(drag.start, clampToCell(point, drag.cell), drag.cell));
    else previewSelection(movedSelection(drag.origin, dx, dy, drag.cell));
  });

  overlay.addEventListener("pointerup", () => {
    const drag = state.drag;
    if (!drag) return;
    state.drag = null;
    if (drag.kind === "lasso" && drag.points.length >= 3) {
      commitSelection(lassoFromPixels(drag.points, drag.cell));
    } else if (drag.kind !== "lasso" && drag.moved) {
      commitSelection(state.live);
    } else if (drag.kind !== "move") {
      // A click (no drag) outside the selection clears it.
      commitSelection({});
    }
  });

  overlay.addEventListener("pointercancel", () => {
    state.drag = null;
    state.live = null;
    applySelection(model.get("selection") || {});
    renderOverlay(theme());
  });

  overlay.addEventListener("pointerleave", () => {
    if (state.hover && !state.drag) {
      state.hover = null;
      renderOverlay(theme());
      renderStatus();
    }
  });

  overlay.addEventListener("dblclick", () => commitSelection({}));
  clearButton.addEventListener("click", () => commitSelection({}));
  keepButton.addEventListener("click", () => addFilter("keep"));
  excludeButton.addEventListener("click", () => addFilter("exclude"));
  resetButton.addEventListener("click", () => setFilters([]));
  layoutButtons.forEach((button) =>
    button.addEventListener("click", () => {
      model.set("layout", button.dataset.layout);
      model.save_changes();
      renderAll();
    })
  );
  modeButtons.forEach((button) =>
    button.addEventListener("click", () => {
      model.set("mode", button.dataset.mode);
      model.save_changes();
      renderStatus();
    })
  );

  // ---- worker ---------------------------------------------------------------

  worker.onmessage = (event) => {
    const data = event.data;
    if (data.type === "error") {
      showError(data.message);
      return;
    }
    if (data.type === "view") {
      // After a data load or a filter change: new active rows, axes and
      // histograms. Any selection result from before is stale.
      clearError();
      // A filter change on the same columns animates from the old axes; the
      // old point sample stays alive as the fading ghost.
      const animate =
        state.filtering &&
        state.extents !== null &&
        state.columns === data.columns &&
        !matchMedia("(prefers-reduced-motion: reduce)").matches;
      const from = animate ? Float64Array.from(shownExtents()) : null;
      const fromTotals = state.histogramTotals;
      stopAnimation();
      let ghost = null;
      if (animate && state.baseMatrixBuffer && state.baseColorBuffer) {
        ghost = { matrix: state.baseMatrixBuffer, colors: state.baseColorBuffer, count: state.sampleCount };
        state.baseMatrixBuffer = null;
        state.baseColorBuffer = null;
      }
      state.filtering = false;
      state.rows = data.rows;
      state.columns = data.columns;
      state.activeCount = data.activeCount;
      state.sampleCount = data.sampleCount;
      state.extents = new Float64Array(data.extents);
      state.histogramTotals = new Uint32Array(data.histogramTotals);
      state.histogramByColor = new Uint32Array(data.histogramByColor);
      state.sampleColors = new Int32Array(data.sampleColors);
      replaceBuffer("baseMatrixBuffer", new Float32Array(data.sampleValues));
      state.dark = null;
      resizeCanvases();
      model.set("status", "ready");
      model.save_changes();
      forgetResult();
      state.appliedKey = null;
      if (ghost) startAnimation(from, fromTotals, ghost);
      const selection = model.get("selection") || {};
      if (selection.type) applySelection(selection);
      else renderAll();
      return;
    }
    if (data.type === "selected") {
      state.inFlight = false;
      if (state.queued) {
        const next = state.queued;
        state.queued = null;
        requestSelection(next);
      }
      if (data.requestId <= state.ignoreUpTo) return;
      state.selectedCount = data.count;
      state.selectedSampleCount = data.sampleCount;
      state.selectedHistogramByColor = new Uint32Array(data.histogramByColor);
      state.selectedColors = new Int32Array(data.sampleColors);
      replaceBuffer("selectedMatrixBuffer", new Float32Array(data.sampleValues));
      state.dark = null;
      renderAll();
    }
  };
  worker.onerror = (event) => showError(`PairPlot worker failed: ${event.message || "unknown error"}`);

  function handleData(message, buffers) {
    if (message.type !== "pair-plot-data" || buffers.length < 2) return;
    clearError();
    statusEl.textContent = "Preparing…";
    state.filtersKey = JSON.stringify(model.get("filters") || []);
    const fullCells = Math.max(1, message.columns * (message.columns - 1));
    const sampleLimit = Math.max(100, Math.floor(model.get("max_marks") / fullCells));
    const matrixBuffer = copyBuffer(buffers[0]);
    const colorBuffer = copyBuffer(buffers[1]);
    worker.postMessage(
      {
        type: "load",
        version: message.version,
        rows: message.rows,
        columns: message.columns,
        categoryCount: Math.max(1, (model.get("palette") || []).length),
        histogramBins: HISTOGRAM_BINS,
        sampleLimit,
        matrixBuffer,
        colorBuffer,
        filters: model.get("filters") || [],
      },
      [matrixBuffer, colorBuffer]
    );
  }

  // ---- model & environment listeners ----------------------------------------

  let frame = 0;
  const scheduleResize = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      resizeCanvases();
      renderAll();
    });
  };
  const handlePalette = () => {
    state.dark = null;
    renderAll();
  };
  const handleSelection = () => applySelection(model.get("selection") || {});
  const requestReload = () => model.send({ type: "ready" });

  model.on("msg:custom", handleData);
  model.on("change:layout", renderAll);
  model.on("change:mode", renderStatus);
  model.on("change:show_filters change:show_mode_toggle change:show_layout_toggle", renderToolbar);
  model.on("change:cell_size", scheduleResize);
  model.on("change:point_size", renderAll);
  model.on("change:palette", handlePalette);
  model.on("change:selection", handleSelection);
  model.on("change:filters", sendFilters);
  model.on("change:max_marks", requestReload);
  model.on("change:data_version", requestReload);

  const resizeObserver = new ResizeObserver(() => {
    if (!model.get("cell_size")) scheduleResize();
  });
  resizeObserver.observe(root);
  // The notebook theme lives on an ancestor's class or attribute, sometimes
  // inside a shadow root that a document-level observer can't see into. So
  // watch every ancestor of the widget (crossing shadow hosts), once it is in
  // the page, and redraw only when the resolved theme actually flips.
  const handleTheme = () => {
    if (state.columns && resolveDark(el) !== state.dark) renderAll();
  };
  const media = matchMedia("(prefers-color-scheme: dark)");
  media.addEventListener("change", handleTheme);
  const themeObserver = new MutationObserver(handleTheme);
  let watchingTheme = false;
  function watchTheme() {
    if (watchingTheme || !el.isConnected) return;
    watchingTheme = true;
    for (let n = el.parentNode || el.host; n; n = n.parentNode || n.host) {
      if (n.nodeType !== 1) continue;
      themeObserver.observe(n, {
        attributes: true,
        attributeFilter: ["class", "data-theme", "data-color-mode", "data-jp-theme-light"],
      });
    }
  }

  model.send({ type: "ready" });

  return () => {
    model.off("msg:custom", handleData);
    model.off("change:layout", renderAll);
    model.off("change:mode", renderStatus);
    model.off("change:show_filters change:show_mode_toggle change:show_layout_toggle", renderToolbar);
    model.off("change:cell_size", scheduleResize);
    model.off("change:point_size", renderAll);
    model.off("change:palette", handlePalette);
    model.off("change:selection", handleSelection);
    model.off("change:filters", sendFilters);
    model.off("change:max_marks", requestReload);
    model.off("change:data_version", requestReload);
    cancelAnimationFrame(frame);
    stopAnimation();
    resizeObserver.disconnect();
    media.removeEventListener("change", handleTheme);
    themeObserver.disconnect();
    worker.terminate();
    URL.revokeObjectURL(workerUrl);
    for (const name of ["baseMatrixBuffer", "baseColorBuffer", "selectedMatrixBuffer", "selectedColorBuffer"]) {
      if (state[name]) state[name].destroy();
    }
    regl.destroy();
  };
}

export default { render };
