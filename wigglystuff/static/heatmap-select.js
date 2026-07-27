// HeatmapSelect — a Bret Victor "Ladder of Abstraction" style parameter-space grid.
//
// Layout is margin-based, like Victor's LadderTimeGrid: the margins around the
// grid ARE the interactive gutters. Hovering the body selects one cell, the left
// gutter selects a row, the bottom gutter selects a column.

const MARGIN_MIN = { left: 30, right: 12, top: 10, bottom: 24 };
const LABEL_GAP = 15;
const LINE_HEIGHT = 11;
const TICK_COUNT = 8;
const TICK_FONT =
  "10px ui-sans-serif, system-ui, -apple-system, 'Helvetica Neue', sans-serif";

// === TICKS (ported from js/bezier-curve/widget.js) ===

function niceTicks(min, max, count = 5) {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [];
  const range = max - min;
  const rough = range / Math.max(1, count);
  const exp = Math.floor(Math.log10(rough));
  const base = Math.pow(10, exp);
  const candidates = [1, 2, 2.5, 5, 10].map((mult) => mult * base);
  const step =
    candidates.find((value) => range / value <= count * 1.5) ??
    candidates[candidates.length - 1];
  const ticks = [];
  const start = Math.ceil(min / step) * step;
  for (let value = start; value <= max + step * 1e-9; value += step) {
    ticks.push(Number((Math.round(value / step) * step).toFixed(12)));
  }
  return ticks;
}

function formatTick(value) {
  if (!Number.isFinite(value)) return "";
  if (value === 0) return "0";
  const abs = Math.abs(value);
  if (abs >= 1000 || abs < 0.01) return value.toExponential(1).replace("e+", "e");
  return value.toFixed(3).replace(/\.?0+$/, "");
}

function clampIndex(value, count) {
  return Math.max(0, Math.min(count - 1, value));
}

// One color per axis is enough — the band fill is the same hue at low alpha.
// Anything that isn't a hex triple is passed through untouched, so rgb()/named
// colors still work (they just can't be given an alpha).
function withAlpha(color, alpha) {
  const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color.trim());
  if (!match) return color;
  const [r, g, b] = [1, 2, 3].map((i) => parseInt(match[i], 16));
  return `rgba(${r},${g},${b},${alpha})`;
}

function render({ model, el }) {
  // === DOM SETUP ===
  const container = document.createElement("div");
  container.className = "heatmap-select";

  const canvas = document.createElement("canvas");
  canvas.className = "heatmap-select__canvas";
  container.appendChild(canvas);
  el.appendChild(container);

  const ctx = canvas.getContext("2d");

  // === STATE ===
  // Three independent pins, one per region. Clicking a region replaces only that
  // region's pin, so a cell, a row and a column can all be held at once.
  // `live` is what the cursor is over right now (null when outside); it is drawn
  // as a faint ghost and never overwrites a pin.
  const pins = { cell: null, row: null, column: null };
  let live = null;
  let isDown = false;
  let imageLoaded = false;
  let throttleTimer = null;
  // Set while we write our own traits, so the change handlers below can tell a
  // Python-side update apart from an echo of our own.
  let applyingLocal = false;

  const gridImage = new Image();
  gridImage.onload = () => {
    imageLoaded = true;
    draw();
  };

  // === GEOMETRY ===

  // The gutters have to fit their tick labels and axis names, so they are
  // measured rather than fixed. Recomputed at the top of draw(); event handlers
  // read the last measured value, which is always current because anything that
  // changes the labels also triggers a redraw.
  const MARGIN = { ...MARGIN_MIN };

  function tickList(axis) {
    const [lo, hi] = model.get(axis === "x" ? "x_range" : "y_range");
    return niceTicks(Math.min(lo, hi), Math.max(lo, hi), TICK_COUNT).filter(
      (tick) => {
        const frac = hi === lo ? 0 : (tick - lo) / (hi - lo);
        return frac >= -1e-9 && frac <= 1 + 1e-9;
      }
    );
  }

  function labelLines(name) {
    const raw = model.get(name);
    return raw ? raw.split("\n") : [];
  }

  function measureMargins() {
    ctx.font = TICK_FONT;
    const widest = (texts) =>
      texts.reduce((max, text) => Math.max(max, ctx.measureText(text).width), 0);

    const yTicks = tickList("y").map(
      (tick) => formatTick(tick) + model.get("y_suffix")
    );
    MARGIN.left = Math.ceil(
      Math.max(MARGIN_MIN.left, widest([...yTicks, ...labelLines("y_label")]) + 10)
    );

    const xLines = labelLines("x_label").length;
    MARGIN.bottom = Math.max(
      MARGIN_MIN.bottom,
      xLines ? LABEL_GAP + 7 + xLines * LINE_HEIGHT : MARGIN_MIN.bottom
    );
  }

  function gridWidth() {
    return model.get("n_cols") * model.get("cell_width");
  }

  function gridHeight() {
    return model.get("n_rows") * model.get("cell_height");
  }

  function totalWidth() {
    return MARGIN.left + gridWidth() + MARGIN.right;
  }

  function totalHeight() {
    return MARGIN.top + gridHeight() + MARGIN.bottom;
  }

  // Data coordinate of a cell center. Ranges name the FIRST and LAST cell
  // centers, so a single-cell axis collapses to its own minimum.
  function colToX(col) {
    const [lo, hi] = model.get("x_range");
    const n = model.get("n_cols");
    return n <= 1 ? lo : lo + (col / (n - 1)) * (hi - lo);
  }

  function rowToY(row) {
    const [lo, hi] = model.get("y_range");
    const n = model.get("n_rows");
    return n <= 1 ? lo : lo + (row / (n - 1)) * (hi - lo);
  }

  // Row 0 of the image sits at the bottom for origin="lower", top for "upper".
  function rowToCanvasY(row) {
    const cellHeight = model.get("cell_height");
    if (model.get("origin") === "lower") {
      return MARGIN.top + gridHeight() - (row + 1) * cellHeight;
    }
    return MARGIN.top + row * cellHeight;
  }

  function canvasYToRow(canvasY) {
    const cellHeight = model.get("cell_height");
    const n = model.get("n_rows");
    const offset = canvasY - MARGIN.top;
    const fromTop = Math.floor(offset / cellHeight);
    const row = model.get("origin") === "lower" ? n - 1 - fromTop : fromTop;
    return clampIndex(row, n);
  }

  function canvasXToCol(canvasX) {
    const offset = canvasX - MARGIN.left;
    return clampIndex(Math.floor(offset / model.get("cell_width")), model.get("n_cols"));
  }

  function getCanvasCoords(event) {
    const rect = canvas.getBoundingClientRect();
    const source = event.touches && event.touches.length ? event.touches[0] : event;
    return {
      x: source.clientX - rect.left,
      y: source.clientY - rect.top,
    };
  }

  // === COLORS ===
  // Canvas can't inherit CSS, so read the theme variables off the container.
  function currentColors() {
    const computed = getComputedStyle(container);
    const read = (name, fallback) =>
      computed.getPropertyValue(name).trim() || fallback;
    return {
      bg: read("--hs-bg", "#ffffff"),
      frame: read("--hs-frame", "#cccccc"),
      tick: read("--hs-tick", "#999999"),
      label: read("--hs-label", "#666666"),
      marker: read("--hs-marker", "#ffffff"),
      markerEdge: read("--hs-marker-edge", "#000000"),
      ghost: read("--hs-ghost", "rgba(140,140,140,0.75)"),
      // An explicit trait wins over the theme, so a caller can match the exact
      // colors their downstream chart uses.
      row: model.get("row_color") || read("--hs-row-color", "#3b82f6"),
      col: model.get("col_color") || read("--hs-col-color", "#f59e0b"),
    };
  }

  // === CANVAS SIZING (devicePixelRatio handling from js/treemap/widget.js) ===

  function syncCanvasSize(width, height) {
    const dpr = window.devicePixelRatio || 1;
    const pixelWidth = Math.max(1, Math.round(width * dpr));
    const pixelHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // === DRAWING ===

  function drawAxes(colors) {
    const gw = gridWidth();
    const gh = gridHeight();
    const bottom = MARGIN.top + gh;

    ctx.font = TICK_FONT;
    ctx.fillStyle = colors.tick;

    // The axis names occupy the origin corner, the way Victor stacks "turning
    // rate" and "bend angle" there — so ticks near the origin are skipped
    // rather than drawn on top of them.
    const xLines = labelLines("x_label");
    const yLines = labelLines("y_label");

    const [xLo, xHi] = model.get("x_range");
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (const tick of tickList("x")) {
      const frac = xHi === xLo ? 0 : (tick - xLo) / (xHi - xLo);
      if (xLines.length && frac < 0.04) continue;
      ctx.fillText(
        formatTick(tick) + model.get("x_suffix"),
        MARGIN.left + frac * gw,
        bottom + 5
      );
    }

    const [yLo, yHi] = model.get("y_range");
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const tick of tickList("y")) {
      const frac = yHi === yLo ? 0 : (tick - yLo) / (yHi - yLo);
      if (yLines.length && frac < 0.05) continue;
      ctx.fillText(
        formatTick(tick) + model.get("y_suffix"),
        MARGIN.left - 6,
        bottom - frac * gh
      );
    }

    // Axis names may carry "\n" to stack onto two lines, the way Victor writes
    // "turning<br>rate" — it lets a long name fit a narrow gutter.
    ctx.fillStyle = colors.label;
    ctx.textAlign = "right";
    ctx.textBaseline = "bottom";
    yLines.forEach((line, i) => {
      ctx.fillText(
        line,
        MARGIN.left - 6,
        bottom - (yLines.length - 1 - i) * LINE_HEIGHT
      );
    });
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    xLines.forEach((line, i) => {
      ctx.fillText(line, MARGIN.left, bottom + LABEL_GAP + 3 + i * LINE_HEIGHT);
    });
  }

  function drawCellMarker(colors, row, col, strong) {
    const cw = model.get("cell_width");
    const ch = model.get("cell_height");
    const x = MARGIN.left + col * cw - 1.5;
    const y = rowToCanvasY(row) - 1.5;
    if (!strong) {
      ctx.lineWidth = 1;
      ctx.strokeStyle = colors.ghost;
      ctx.strokeRect(x, y, cw + 3, ch + 3);
      return;
    }
    // A hollow square, drawn twice so it reads against both black and white
    // cells — Victor uses a single PNG that only works on his palette.
    ctx.lineWidth = 3;
    ctx.strokeStyle = colors.markerEdge;
    ctx.strokeRect(x, y, cw + 3, ch + 3);
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = colors.marker;
    ctx.strokeRect(x, y, cw + 3, ch + 3);
  }

  function drawBand(rect, color, strong) {
    if (strong) {
      ctx.fillStyle = withAlpha(color, 0.22);
      ctx.fillRect(rect.x, rect.y, rect.w, rect.h);
    }
    ctx.lineWidth = strong ? 1.5 : 1;
    ctx.strokeStyle = withAlpha(color, strong ? 0.95 : 0.5);
    ctx.strokeRect(rect.x + 0.5, rect.y + 0.5, rect.w - 1, rect.h - 1);
  }

  function drawRowBand(colors, row, strong) {
    // Spans the full width including the gutters, so the band visually ties the
    // y axis to the data it selects.
    const ch = model.get("cell_height");
    const y = rowToCanvasY(row);
    drawBand({ x: 2, y: y - 2, w: totalWidth() - 4, h: ch + 4 }, colors.row, strong);
  }

  function drawColumnBand(colors, col, strong) {
    const cw = model.get("cell_width");
    const x = MARGIN.left + col * cw;
    drawBand(
      { x: x - 2, y: 2, w: cw + 4, h: totalHeight() - 4 },
      colors.col,
      strong
    );
  }

  function drawSelection(colors, selection, strong) {
    if (selection.mode === "cell") {
      drawCellMarker(colors, selection.row, selection.col, strong);
    } else if (selection.mode === "row") {
      drawRowBand(colors, selection.row, strong);
    } else if (selection.mode === "column") {
      drawColumnBand(colors, selection.col, strong);
    }
  }

  function sameSelection(a, b) {
    if (!a || !b) return false;
    return a.mode === b.mode && a.row === b.row && a.col === b.col;
  }

  function draw() {
    measureMargins();
    const width = totalWidth();
    const height = totalHeight();
    syncCanvasSize(width, height);

    const colors = currentColors();
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, width, height);

    if (imageLoaded) {
      // One image pixel per cell, blown up with no smoothing so cells stay
      // crisp squares rather than a blurry gradient.
      ctx.imageSmoothingEnabled = false;
      ctx.save();
      if (model.get("origin") === "lower") {
        // Row 0 of the image belongs at the bottom, matching imshow's
        // origin="lower". The bitmap has to flip too, or it ends up mirrored
        // against the axis ticks and the marker.
        ctx.translate(MARGIN.left, MARGIN.top + gridHeight());
        ctx.scale(1, -1);
      } else {
        ctx.translate(MARGIN.left, MARGIN.top);
      }
      ctx.drawImage(gridImage, 0, 0, gridWidth(), gridHeight());
      ctx.restore();
      ctx.imageSmoothingEnabled = true;
    }

    ctx.lineWidth = 1;
    ctx.strokeStyle = colors.frame;
    ctx.strokeRect(
      MARGIN.left - 0.5,
      MARGIN.top - 0.5,
      gridWidth() + 1,
      gridHeight() + 1
    );

    drawAxes(colors);

    // Pins are drawn strong and stay put; hover is a faint ghost that never
    // displaces them. Bands go down first so the small cell marker stays legible
    // on top of them.
    if (pins.row) drawSelection(colors, pins.row, true);
    if (pins.column) drawSelection(colors, pins.column, true);
    if (live && !sameSelection(live, pins[live.mode])) {
      drawSelection(colors, live, false);
    }
    if (pins.cell) drawSelection(colors, pins.cell, true);
  }

  // === MODEL SYNC ===

  function syncToModel() {
    model.save_changes();
  }

  function throttledSync() {
    const throttle = model.get("throttle");
    if (throttle === "dragend") return;
    if (throttle === 0) {
      syncToModel();
      return;
    }
    if (throttleTimer === null) {
      throttleTimer = setTimeout(() => {
        throttleTimer = null;
        syncToModel();
      }, throttle);
    }
  }

  function flushSync() {
    if (throttleTimer !== null) {
      clearTimeout(throttleTimer);
      throttleTimer = null;
    }
    syncToModel();
  }

  // Writes the three pins and the single hover into the six traits. Cells go out
  // as [row, col]; rows and columns as a bare index; null means "nothing here".
  function publish() {
    applyingLocal = true;
    model.set("pinned_cell", pins.cell ? [pins.cell.row, pins.cell.col] : null);
    model.set("pinned_row", pins.row ? pins.row.row : null);
    model.set("pinned_col", pins.column ? pins.column.col : null);
    model.set("hover_cell", live?.mode === "cell" ? [live.row, live.col] : null);
    model.set("hover_row", live?.mode === "row" ? live.row : null);
    model.set("hover_col", live?.mode === "column" ? live.col : null);
    applyingLocal = false;
  }

  // Sweeping the cursor inside one cell republishes identical values, so skip the
  // round trip rather than spamming the kernel with no-op updates.
  let lastPublished = null;

  function publishAndSync(immediate) {
    publish();
    const signature = JSON.stringify([
      model.get("pinned_cell"),
      model.get("pinned_row"),
      model.get("pinned_col"),
      model.get("hover_cell"),
      model.get("hover_row"),
      model.get("hover_col"),
    ]);
    if (signature === lastPublished) return;
    lastPublished = signature;
    if (immediate) flushSync();
    else throttledSync();
  }

  // === EVENT HANDLERS ===

  // Mode is decided purely by which region the cursor is in, mirroring
  // LadderTimeGrid.cursorMovedToPoint: left gutter sweeps x (a row band),
  // bottom gutter sweeps y (a column band), the body picks a single cell.
  function selectionAt(coords) {
    const row = canvasYToRow(coords.y);
    const col = canvasXToCol(coords.x);
    if (coords.x < MARGIN.left) return { mode: "row", row, col };
    if (coords.y > MARGIN.top + gridHeight()) return { mode: "column", row, col };
    return { mode: "cell", row, col };
  }

  function handleMove(event) {
    live = selectionAt(getCanvasCoords(event));
    // Dragging keeps moving that region's pin; a plain hover never moves a pin.
    if (isDown) pins[live.mode] = { ...live };
    publishAndSync(false);
    draw();
  }

  // A click commits the region under the cursor — including either gutter, so you
  // can click an axis to hold a whole row or column. Only that region's pin is
  // replaced; the other two stay exactly where they were.
  function handleDown(event) {
    event.preventDefault();
    isDown = true;
    live = selectionAt(getCanvasCoords(event));
    pins[live.mode] = { ...live };
    publishAndSync(true);
    draw();
  }

  function handleUp() {
    if (!isDown) return;
    isDown = false;
    flushSync();
  }

  function handleLeave() {
    isDown = false;
    live = null;
    publishAndSync(true);
    draw();
  }

  // Symmetric with clicking: double-click drops the pin belonging to the region
  // you double-clicked in, and leaves the other two alone.
  function handleDoubleClick(event) {
    event.preventDefault();
    const region = selectionAt(getCanvasCoords(event));
    pins[region.mode] = null;
    live = region;
    publishAndSync(true);
    draw();
  }

  // === EVENT BINDING ===
  canvas.addEventListener("mousemove", handleMove);
  canvas.addEventListener("mousedown", handleDown);
  canvas.addEventListener("mouseup", handleUp);
  canvas.addEventListener("mouseleave", handleLeave);
  canvas.addEventListener("dblclick", handleDoubleClick);
  canvas.addEventListener("touchstart", handleDown, { passive: false });
  canvas.addEventListener("touchmove", (event) => {
    event.preventDefault();
    handleMove(event);
  }, { passive: false });
  canvas.addEventListener("touchend", handleUp);
  window.addEventListener("mouseup", handleUp);

  // === MODEL WIRING ===
  gridImage.src = model.get("image_base64");
  model.on("change:image_base64", () => {
    imageLoaded = false;
    gridImage.src = model.get("image_base64");
  });
  for (const name of [
    "n_rows",
    "n_cols",
    "cell_width",
    "cell_height",
    "x_range",
    "y_range",
    "x_label",
    "y_label",
    "x_suffix",
    "y_suffix",
    "origin",
    "row_color",
    "col_color",
  ]) {
    model.on("change:" + name, draw);
  }
  // Pins set from Python (clear(), or assigning a trait directly) have to land
  // back in the JS state, or the next redraw would resurrect the old ones.
  function adoptPinsFromModel() {
    if (applyingLocal) return;
    const cell = model.get("pinned_cell");
    const row = model.get("pinned_row");
    const col = model.get("pinned_col");
    pins.cell = cell ? { mode: "cell", row: cell[0], col: cell[1] } : null;
    pins.row = row === null ? null : { mode: "row", row, col: -1 };
    pins.column = col === null ? null : { mode: "column", row: -1, col };
    lastPublished = null;
    draw();
  }

  for (const name of ["pinned_cell", "pinned_row", "pinned_col"]) {
    model.on("change:" + name, adoptPinsFromModel);
  }

  // Seed from the traits rather than from nothing. The widget can be re-rendered
  // at any time — displayed in a second place, or re-mounted when its host cell
  // re-runs — and the pins have to come back rather than silently vanish.
  adoptPinsFromModel();

  return () => {
    window.removeEventListener("mouseup", handleUp);
    if (throttleTimer !== null) clearTimeout(throttleTimer);
  };
}

export default { render };
