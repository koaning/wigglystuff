import {
  canonicalSegment,
  pointKey,
  segmentKey,
  segmentUnderPosition,
  traceSegmentsBetweenPositions,
} from "./geometry.mjs";

function makeSvgElement(tag) {
  return document.createElementNS("http://www.w3.org/2000/svg", tag);
}

function sortedDots(dotMap) {
  return Array.from(dotMap.values()).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
}

function sortedLines(lineMap) {
  return Array.from(lineMap.values()).sort(
    (a, b) =>
      a.from[0] - b.from[0] ||
      a.from[1] - b.from[1] ||
      a.to[0] - b.to[0] ||
      a.to[1] - b.to[1],
  );
}

function normalizeDots(rawDots) {
  const dots = new Map();
  for (const dot of rawDots || []) {
    if (!Array.isArray(dot) || dot.length !== 2) {
      continue;
    }
    dots.set(pointKey(dot), [dot[0], dot[1]]);
  }
  return dots;
}

function normalizeLines(rawLines) {
  const lines = new Map();
  for (const line of rawLines || []) {
    if (!line || !Array.isArray(line.from) || !Array.isArray(line.to)) {
      continue;
    }
    const [from, to] = canonicalSegment(line.from, line.to);
    lines.set(segmentKey(from, to), {
      from: [from[0], from[1]],
      to: [to[0], to[1]],
      width: line.width,
    });
  }
  return lines;
}

function defaultLineWidth(lineWidth) {
  return Array.isArray(lineWidth) ? lineWidth[0] : lineWidth;
}

const ICONS = {
  dot: [
    ["circle", { cx: 12, cy: 12, r: 10 }],
    ["circle", { cx: 12, cy: 12, r: 2 }],
  ],
  line: [["path", { d: "M5 12h14" }]],
  erase: [
    ["path", { d: "m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21" }],
    ["path", { d: "M22 21H7" }],
    ["path", { d: "m5 11 9 9" }],
  ],
  undo: [
    ["path", { d: "M9 14 4 9l5-5" }],
    ["path", { d: "M4 9h10.5a5.5 5.5 0 0 1 0 11H11" }],
  ],
  clear: [
    ["path", { d: "M3 6h18" }],
    ["path", { d: "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" }],
    ["path", { d: "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" }],
    ["line", { x1: 10, x2: 10, y1: 11, y2: 17 }],
    ["line", { x1: 14, x2: 14, y1: 11, y2: 17 }],
  ],
  theme: [
    ["path", { d: "M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" }],
    ["path", { d: "M12 2v2" }],
    ["path", { d: "M12 20v2" }],
    ["path", { d: "m4.93 4.93 1.41 1.41" }],
    ["path", { d: "m17.66 17.66 1.41 1.41" }],
    ["path", { d: "M2 12h2" }],
    ["path", { d: "M20 12h2" }],
  ],
};

function icon(name) {
  const svg = makeSvgElement("svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.classList.add("gd-icon");
  for (const [tag, attrs] of ICONS[name]) {
    const child = makeSvgElement(tag);
    for (const [attr, value] of Object.entries(attrs)) {
      child.setAttribute(attr, value);
    }
    svg.appendChild(child);
  }
  return svg;
}

function render({ model, el }) {
  el.replaceChildren();

  const root = document.createElement("div");
  root.className = "griddraw";
  el.appendChild(root);

  const toolbar = document.createElement("div");
  toolbar.className = "gd-toolbar";
  root.appendChild(toolbar);

  const svg = makeSvgElement("svg");
  svg.classList.add("gd-canvas");
  root.appendChild(svg);

  let mode = "dot";
  let dots = normalizeDots(model.get("dots"));
  let lines = normalizeLines(model.get("lines"));
  let rows = model.get("rows");
  let cols = model.get("cols");
  let dotRadius = model.get("dot_radius");
  let lineWidth = model.get("line_width");
  let currentWidth = defaultLineWidth(lineWidth);
  let localTheme = model.get("theme");
  let undoStack = [];
  let gesture = null;
  let syncing = false;

  const modeButtons = new Map();
  const widthSelect = document.createElement("select");
  widthSelect.className = "gd-width-select";
  widthSelect.title = "Line width";
  widthSelect.setAttribute("aria-label", "Line width");

  function button(iconName, label, title, onClick) {
    const item = document.createElement("button");
    item.type = "button";
    item.title = title;
    item.setAttribute("aria-label", title);
    item.appendChild(icon(iconName));
    const text = document.createElement("span");
    text.className = "gd-button-label";
    text.textContent = label;
    item.appendChild(text);
    item.addEventListener("click", onClick);
    toolbar.appendChild(item);
    return item;
  }

  function setMode(nextMode) {
    mode = nextMode;
    for (const [buttonMode, item] of modeButtons) {
      item.classList.toggle("active", buttonMode === mode);
    }
  }

  modeButtons.set("dot", button("dot", "Dot", "Dot mode", () => setMode("dot")));
  modeButtons.set("line", button("line", "Line", "Line mode", () => setMode("line")));
  modeButtons.set("erase", button("erase", "Erase", "Eraser mode", () => setMode("erase")));
  button("undo", "Undo", "Undo", undo);
  button("clear", "Clear", "Clear", clearDrawing);
  button("theme", "Theme", "Toggle theme", toggleTheme);
  toolbar.appendChild(widthSelect);
  widthSelect.addEventListener("change", () => {
    currentWidth = Number(widthSelect.value);
  });
  setMode("dot");

  function snapshot() {
    return {
      dots: sortedDots(dots).map((dot) => [...dot]),
      lines: sortedLines(lines).map((line) => ({
        from: [...line.from],
        to: [...line.to],
        width: line.width,
      })),
    };
  }

  function restore(state) {
    dots = normalizeDots(state.dots);
    lines = normalizeLines(state.lines);
    syncModel();
    draw();
  }

  function pushUndo() {
    undoStack.push(snapshot());
    if (undoStack.length > 100) {
      undoStack.shift();
    }
  }

  function undo() {
    const previous = undoStack.pop();
    if (previous) {
      restore(previous);
    }
  }

  function clearDrawing() {
    if (dots.size === 0 && lines.size === 0) {
      return;
    }
    pushUndo();
    dots = new Map();
    lines = new Map();
    syncModel();
    draw();
  }

  function toggleTheme() {
    const current =
      localTheme ||
      (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light");
    localTheme = current === "dark" ? "light" : "dark";
    root.dataset.theme = localTheme;
    syncing = true;
    model.set("theme", localTheme);
    model.save_changes();
    syncing = false;
  }

  function syncModel() {
    syncing = true;
    model.set("dots", sortedDots(dots));
    model.set("lines", sortedLines(lines));
    model.save_changes();
    syncing = false;
  }

  function updateToolbar() {
    widthSelect.replaceChildren();
    const options = Array.isArray(lineWidth) ? lineWidth : [];
    widthSelect.hidden = options.length === 0;
    for (const width of options) {
      const option = document.createElement("option");
      option.value = String(width);
      option.textContent = `${width}px`;
      option.selected = width === currentWidth;
      widthSelect.appendChild(option);
    }
  }

  function updateTheme() {
    if (localTheme) {
      root.dataset.theme = localTheme;
    } else {
      delete root.dataset.theme;
    }
  }

  function layout() {
    const width = model.get("width");
    const height = model.get("height");
    const maxLineWidth = Array.isArray(lineWidth) ? Math.max(...lineWidth) : lineWidth;
    const padding = Math.max(18, dotRadius + maxLineWidth + 8);
    const plotWidth = Math.max(1, width - padding * 2);
    const plotHeight = Math.max(1, height - padding * 2);
    return {
      width,
      height,
      rows,
      cols,
      padding,
      plotWidth,
      plotHeight,
      cellWidth: plotWidth / cols,
      cellHeight: plotHeight / rows,
    };
  }

  function xy(point, box) {
    return {
      x: box.padding + point[1] * box.cellWidth,
      y: box.padding + point[0] * box.cellHeight,
    };
  }

  function clearSvg() {
    while (svg.firstChild) {
      svg.removeChild(svg.firstChild);
    }
  }

  function draw() {
    updateToolbar();
    updateTheme();
    const box = layout();
    root.style.width = `${box.width}px`;
    svg.setAttribute("width", box.width);
    svg.setAttribute("height", box.height);
    svg.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
    clearSvg();

    const gridGroup = makeSvgElement("g");
    gridGroup.classList.add("gd-grid");
    svg.appendChild(gridGroup);
    for (let row = 0; row <= rows; row += 1) {
      const y = box.padding + row * box.cellHeight;
      const line = makeSvgElement("line");
      line.setAttribute("x1", box.padding);
      line.setAttribute("x2", box.padding + box.plotWidth);
      line.setAttribute("y1", y);
      line.setAttribute("y2", y);
      gridGroup.appendChild(line);
    }
    for (let col = 0; col <= cols; col += 1) {
      const x = box.padding + col * box.cellWidth;
      const line = makeSvgElement("line");
      line.setAttribute("x1", x);
      line.setAttribute("x2", x);
      line.setAttribute("y1", box.padding);
      line.setAttribute("y2", box.padding + box.plotHeight);
      gridGroup.appendChild(line);
    }

    const placeholders = makeSvgElement("g");
    placeholders.classList.add("gd-placeholders");
    svg.appendChild(placeholders);
    for (let row = 0; row <= rows; row += 1) {
      for (let col = 0; col <= cols; col += 1) {
        const circle = makeSvgElement("circle");
        const pos = xy([row, col], box);
        circle.setAttribute("cx", pos.x);
        circle.setAttribute("cy", pos.y);
        circle.setAttribute("r", 2);
        placeholders.appendChild(circle);
      }
    }

    const lineGroup = makeSvgElement("g");
    lineGroup.classList.add("gd-lines");
    svg.appendChild(lineGroup);
    for (const line of sortedLines(lines)) {
      const start = xy(line.from, box);
      const end = xy(line.to, box);
      const item = makeSvgElement("line");
      item.setAttribute("x1", start.x);
      item.setAttribute("y1", start.y);
      item.setAttribute("x2", end.x);
      item.setAttribute("y2", end.y);
      item.setAttribute("stroke-width", line.width);
      lineGroup.appendChild(item);
    }

    const dotGroup = makeSvgElement("g");
    dotGroup.classList.add("gd-dots");
    svg.appendChild(dotGroup);
    for (const dot of sortedDots(dots)) {
      const pos = xy(dot, box);
      const circle = makeSvgElement("circle");
      circle.setAttribute("cx", pos.x);
      circle.setAttribute("cy", pos.y);
      circle.setAttribute("r", dotRadius);
      dotGroup.appendChild(circle);
    }
  }

  function pointerPosition(event) {
    const rect = svg.getBoundingClientRect();
    const box = layout();
    return {
      x: ((event.clientX - rect.left) / rect.width) * box.width,
      y: ((event.clientY - rect.top) / rect.height) * box.height,
    };
  }

  function nearestPoint(pos) {
    const box = layout();
    const col = Math.round((pos.x - box.padding) / box.cellWidth);
    const row = Math.round((pos.y - box.padding) / box.cellHeight);
    if (row < 0 || row > rows || col < 0 || col > cols) {
      return null;
    }
    const snapped = xy([row, col], box);
    const distance = Math.hypot(pos.x - snapped.x, pos.y - snapped.y);
    const tolerance = Math.max(10, Math.min(box.cellWidth, box.cellHeight) * 0.35);
    return distance <= tolerance ? [row, col] : null;
  }

  function segmentUnderPointer(pos) {
    return segmentUnderPosition(pos, layout());
  }

  function addDot(point) {
    if (point) {
      dots.set(pointKey(point), point);
    }
  }

  function removeDot(point) {
    if (point) {
      dots.delete(pointKey(point));
    }
  }

  function addLine(from, to) {
    const [start, end] = canonicalSegment(from, to);
    lines.set(segmentKey(start, end), {
      from: [start[0], start[1]],
      to: [end[0], end[1]],
      width: currentWidth,
    });
  }

  function removeLine(from, to) {
    const [start, end] = canonicalSegment(from, to);
    lines.delete(segmentKey(start, end));
  }

  function toggleDot(point) {
    if (!point) {
      return;
    }
    const key = pointKey(point);
    if (dots.has(key)) {
      dots.delete(key);
    } else {
      dots.set(key, point);
    }
  }

  function toggleLine(segment) {
    if (!segment) {
      return;
    }
    const key = segmentKey(segment.from, segment.to);
    if (lines.has(key)) {
      lines.delete(key);
    } else {
      addLine(segment.from, segment.to);
    }
  }

  function applyDrag(event) {
    if (!gesture) {
      return;
    }
    const pos = pointerPosition(event);
    const point = nearestPoint(pos);
    const segment = segmentUnderPointer(pos);
    const moved = Math.hypot(pos.x - gesture.start.x, pos.y - gesture.start.y) > 4;
    if (moved) {
      gesture.dragged = true;
    }

    if (!gesture.dragged) {
      return;
    }

    if (!gesture.didPaintStart) {
      if (mode === "dot") {
        addDot(gesture.startPoint);
      } else if (mode === "erase") {
        removeDot(gesture.startPoint);
        if (gesture.startSegment) {
          removeLine(gesture.startSegment.from, gesture.startSegment.to);
        }
      } else if (mode === "line" && gesture.startSegment) {
        addLine(gesture.startSegment.from, gesture.startSegment.to);
      }
      gesture.didPaintStart = true;
    }

    if (mode === "dot") {
      addDot(point);
    } else if (mode === "erase") {
      removeDot(point);
      if (segment) {
        removeLine(segment.from, segment.to);
      }
      if (gesture.lastPos) {
        for (const tracedSegment of traceSegmentsBetweenPositions(gesture.lastPos, pos, layout())) {
          removeLine(tracedSegment.from, tracedSegment.to);
        }
      }
    } else if (mode === "line" && gesture.lastPos) {
      for (const tracedSegment of traceSegmentsBetweenPositions(gesture.lastPos, pos, layout())) {
        addLine(tracedSegment.from, tracedSegment.to);
      }
    }

    if (point) {
      gesture.lastPoint = point;
    }
    gesture.lastPos = pos;
    syncModel();
    draw();
  }

  svg.addEventListener("pointerdown", (event) => {
    root.focus();
    svg.setPointerCapture(event.pointerId);
    const pos = pointerPosition(event);
    pushUndo();
    gesture = {
      pointerId: event.pointerId,
      start: pos,
      startPoint: nearestPoint(pos),
      startSegment: segmentUnderPointer(pos),
      lastPoint: nearestPoint(pos),
      lastPos: pos,
      dragged: false,
      didPaintStart: false,
    };
  });

  svg.addEventListener("pointermove", applyDrag);

  svg.addEventListener("pointerup", (event) => {
    if (!gesture) {
      return;
    }
    const pos = pointerPosition(event);
    if (!gesture.dragged) {
      if (mode === "dot") {
        toggleDot(nearestPoint(pos));
      } else if (mode === "line") {
        toggleLine(segmentUnderPointer(pos));
      } else {
        removeDot(nearestPoint(pos));
        const segment = segmentUnderPointer(pos);
        if (segment) {
          removeLine(segment.from, segment.to);
        }
      }
      syncModel();
      draw();
    }
    svg.releasePointerCapture(event.pointerId);
    gesture = null;
  });

  svg.addEventListener("pointercancel", () => {
    gesture = null;
  });

  root.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") {
      event.preventDefault();
      undo();
    }
  });
  root.tabIndex = 0;

  model.on("change:dots", () => {
    if (syncing) {
      return;
    }
    dots = normalizeDots(model.get("dots"));
    draw();
  });

  model.on("change:lines", () => {
    if (syncing) {
      return;
    }
    lines = normalizeLines(model.get("lines"));
    draw();
  });

  model.on("change:rows change:cols change:dot_radius change:width change:height change:line_width", () => {
    rows = model.get("rows");
    cols = model.get("cols");
    dotRadius = model.get("dot_radius");
    lineWidth = model.get("line_width");
    currentWidth = defaultLineWidth(lineWidth);
    draw();
  });

  model.on("change:theme", () => {
    if (syncing) {
      return;
    }
    localTheme = model.get("theme");
    draw();
  });

  draw();
}

export default { render };
