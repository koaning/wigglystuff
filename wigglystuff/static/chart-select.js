function render({ model, el }) {
  // === DOM SETUP ===
  const container = document.createElement("div");
  container.className = "chart-select";

  const canvas = document.createElement("canvas");
  canvas.width = model.get("width");
  canvas.height = model.get("height");
  canvas.className = "chart-select__canvas";

  // SVG icons
  const boxIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="2" y="2" width="10" height="10" rx="1"/>
  </svg>`;
  const lassoIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M7 2C4 2 2 4.5 2 7c0 2 1 3.5 3 4M10 11c1.5-1 2-2.5 2-4 0-2.5-2-5-5-5"/>
    <circle cx="5" cy="11" r="1.5" fill="currentColor"/>
  </svg>`;

  // Available modes from model
  const availableModes = model.get("modes") || ["box", "lasso"];
  const modeConfig = [
    { mode: "box", icon: boxIcon, label: "Box" },
    { mode: "lasso", icon: lassoIcon, label: "Lasso" },
  ].filter((m) => availableModes.includes(m.mode));

  const modes = modeConfig.map((m) => m.mode);
  const modeButtons = {};

  // Only show controls if more than one mode is available
  let controls = null;
  if (modeConfig.length > 1) {
    controls = document.createElement("div");
    controls.className = "chart-select__controls";

    modeConfig.forEach(({ mode, icon, label }) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chart-select__mode-btn";
      btn.dataset.mode = mode;
      btn.innerHTML = `<span class="chart-select__icon">${icon}</span><span class="chart-select__label">${label}</span>`;
      btn.title = label;
      btn.addEventListener("click", () => setMode(mode));
      controls.appendChild(btn);
      modeButtons[mode] = btn;
    });

    container.appendChild(controls);
  } else {
    // No controls - canvas needs full rounded corners
    canvas.classList.add("chart-select__canvas--no-controls");
  }

  container.appendChild(canvas);
  el.appendChild(container);

  // === STATE ===
  const ctx = canvas.getContext("2d");
  const chartImage = new Image();
  let imageLoaded = false;
  let currentMode = model.get("mode");

  // Selection state
  let isSelecting = false;
  let isDragging = false;
  let selectionStart = null;
  let dragStart = null;
  let lassoPath = [];

  // === COORDINATE TRANSFORMS ===
  function pixelToData(pixelX, pixelY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    // Clamp to axes area
    pixelX = Math.max(left, Math.min(right, pixelX));
    pixelY = Math.max(top, Math.min(bottom, pixelY));

    const dataX = xMin + ((pixelX - left) / (right - left)) * (xMax - xMin);
    const dataY = yMin + ((bottom - pixelY) / (bottom - top)) * (yMax - yMin);

    return { x: dataX, y: dataY };
  }

  function dataToPixel(dataX, dataY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    const pixelX = left + ((dataX - xMin) / (xMax - xMin)) * (right - left);
    const pixelY = bottom - ((dataY - yMin) / (yMax - yMin)) * (bottom - top);
    return { x: pixelX, y: pixelY };
  }

  function isInsideAxes(coords) {
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");
    return coords.x >= left && coords.x <= right && coords.y >= top && coords.y <= bottom;
  }

  function isInsideSelection(coords) {
    if (!model.get("has_selection")) return false;
    const selection = model.get("selection");
    const mode = model.get("mode");

    if (mode === "box" && selection.x_min !== undefined) {
      const topLeft = dataToPixel(selection.x_min, selection.y_max);
      const bottomRight = dataToPixel(selection.x_max, selection.y_min);
      return (
        coords.x >= topLeft.x &&
        coords.x <= bottomRight.x &&
        coords.y >= topLeft.y &&
        coords.y <= bottomRight.y
      );
    } else if (selection.vertices && selection.vertices.length >= 3) {
      // Point-in-polygon test for lasso
      const pixelVertices = selection.vertices.map((v) => dataToPixel(v[0], v[1]));
      return pointInPolygon(coords, pixelVertices);
    }
    return false;
  }

  function pointInPolygon(point, vertices) {
    let inside = false;
    for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i++) {
      const xi = vertices[i].x, yi = vertices[i].y;
      const xj = vertices[j].x, yj = vertices[j].y;
      if (((yi > point.y) !== (yj > point.y)) &&
          (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    return inside;
  }

  // === MODE MANAGEMENT ===
  function setMode(mode) {
    currentMode = mode;
    model.set("mode", mode);
    model.save_changes();
    updateModeButtons();
    isSelecting = false;
    isDragging = false;
    lassoPath = [];
    selectionStart = null;
    dragStart = null;
    draw();
  }

  function updateModeButtons() {
    modes.forEach((mode) => {
      if (modeButtons[mode]) {
        modeButtons[mode].classList.toggle("active", mode === currentMode);
      }
    });
  }

  // === SELECTION LOGIC ===
  function clearSelection() {
    model.set("selection", {});
    model.set("has_selection", false);
    model.save_changes();
    isSelecting = false;
    isDragging = false;
    lassoPath = [];
    selectionStart = null;
    dragStart = null;
    draw();
  }

  function getCanvasCoords(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY,
    };
  }

  // === EVENT HANDLERS ===
  function handleMouseDown(event) {
    event.preventDefault();
    const coords = getCanvasCoords(event);

    // Check if clicking inside existing selection (to drag it)
    if (model.get("has_selection") && isInsideSelection(coords)) {
      isDragging = true;
      dragStart = coords;
      return;
    }

    // If there's a selection and we clicked outside it, clear it
    if (model.get("has_selection")) {
      clearSelection();
      // Don't start a new selection on the same click
      return;
    }

    // Check if clicking outside axes area - do nothing
    if (!isInsideAxes(coords)) {
      return;
    }

    // Start new selection
    if (currentMode === "box") {
      isSelecting = true;
      selectionStart = coords;
    } else if (currentMode === "lasso") {
      isSelecting = true;
      lassoPath = [coords];
    }
  }

  function handleMouseMove(event) {
    const coords = getCanvasCoords(event);

    // Handle dragging existing selection
    if (isDragging && dragStart) {
      const dx = coords.x - dragStart.x;
      const dy = coords.y - dragStart.y;
      moveSelection(dx, dy);
      dragStart = coords;
      return;
    }

    // Update cursor based on hover state
    if (model.get("has_selection") && isInsideSelection(coords)) {
      canvas.style.cursor = "move";
    } else {
      canvas.style.cursor = "crosshair";
    }

    // Handle creating new selection
    if (currentMode === "box" && isSelecting) {
      draw();
      drawBoxPreview(selectionStart, coords);
    } else if (currentMode === "lasso" && isSelecting) {
      lassoPath.push(coords);
      draw();
      drawLassoPreview(lassoPath);
    }
  }

  function handleMouseUp(event) {
    const coords = getCanvasCoords(event);

    if (isDragging) {
      isDragging = false;
      dragStart = null;
      return;
    }

    if (currentMode === "box" && isSelecting) {
      const startData = pixelToData(selectionStart.x, selectionStart.y);
      const endData = pixelToData(coords.x, coords.y);

      // Only create selection if it has some size
      const width = Math.abs(endData.x - startData.x);
      const height = Math.abs(endData.y - startData.y);
      if (width > 0.01 || height > 0.01) {
        const selection = {
          x_min: Math.min(startData.x, endData.x),
          y_min: Math.min(startData.y, endData.y),
          x_max: Math.max(startData.x, endData.x),
          y_max: Math.max(startData.y, endData.y),
        };
        model.set("selection", selection);
        model.set("has_selection", true);
        model.save_changes();
      }

      isSelecting = false;
      selectionStart = null;
    } else if (currentMode === "lasso" && isSelecting) {
      if (lassoPath.length >= 3) {
        const vertices = lassoPath.map((p) => {
          const d = pixelToData(p.x, p.y);
          return [d.x, d.y];
        });
        model.set("selection", { vertices });
        model.set("has_selection", true);
        model.save_changes();
      }
      isSelecting = false;
      lassoPath = [];
    }

    draw();
  }

  function moveSelection(dx, dy) {
    const selection = model.get("selection");
    const mode = model.get("mode");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

    // Convert pixel delta to data delta
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const dataWidth = xMax - xMin;
    const dataHeight = yMax - yMin;
    const pixelWidth = right - left;
    const pixelHeight = bottom - top;

    const ddx = (dx / pixelWidth) * dataWidth;
    const ddy = -(dy / pixelHeight) * dataHeight; // Inverted Y

    if (mode === "box" && selection.x_min !== undefined) {
      const newSelection = {
        x_min: selection.x_min + ddx,
        y_min: selection.y_min + ddy,
        x_max: selection.x_max + ddx,
        y_max: selection.y_max + ddy,
      };
      model.set("selection", newSelection);
      model.save_changes();
    } else if (selection.vertices) {
      const newVertices = selection.vertices.map((v) => [v[0] + ddx, v[1] + ddy]);
      model.set("selection", { vertices: newVertices });
      model.save_changes();
    }

    draw();
  }

  // === DRAWING ===
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (imageLoaded) {
      ctx.drawImage(chartImage, 0, 0);
    }

    if (model.get("has_selection")) {
      drawSelection();
    }
  }

  function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function drawSelection() {
    const selection = model.get("selection");
    const color = model.get("selection_color");
    const opacity = model.get("selection_opacity");
    const strokeWidth = model.get("stroke_width");

    ctx.save();
    ctx.fillStyle = hexToRgba(color, opacity);
    ctx.strokeStyle = color;
    ctx.lineWidth = strokeWidth;

    const mode = model.get("mode");
    if (mode === "box" && selection.x_min !== undefined) {
      const topLeft = dataToPixel(selection.x_min, selection.y_max);
      const bottomRight = dataToPixel(selection.x_max, selection.y_min);
      const w = bottomRight.x - topLeft.x;
      const h = bottomRight.y - topLeft.y;

      ctx.fillRect(topLeft.x, topLeft.y, w, h);
      ctx.strokeRect(topLeft.x, topLeft.y, w, h);
    } else if (selection.vertices && selection.vertices.length >= 3) {
      ctx.beginPath();
      const first = dataToPixel(selection.vertices[0][0], selection.vertices[0][1]);
      ctx.moveTo(first.x, first.y);

      for (let i = 1; i < selection.vertices.length; i++) {
        const p = dataToPixel(selection.vertices[i][0], selection.vertices[i][1]);
        ctx.lineTo(p.x, p.y);
      }

      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    ctx.restore();
  }

  function drawBoxPreview(start, end) {
    const color = model.get("selection_color");
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(
      Math.min(start.x, end.x),
      Math.min(start.y, end.y),
      Math.abs(end.x - start.x),
      Math.abs(end.y - start.y)
    );
    ctx.restore();
  }

  function drawLassoPreview(path) {
    if (path.length < 2) return;

    const color = model.get("selection_color");
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(path[0].x, path[0].y);
    for (let i = 1; i < path.length; i++) {
      ctx.lineTo(path[i].x, path[i].y);
    }
    ctx.stroke();
    ctx.restore();
  }

  // === EVENT BINDING ===
  canvas.addEventListener("mousedown", handleMouseDown);
  canvas.addEventListener("mousemove", handleMouseMove);
  canvas.addEventListener("mouseup", handleMouseUp);

  // Touch support
  canvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
    const touch = e.touches[0];
    handleMouseDown({
      clientX: touch.clientX,
      clientY: touch.clientY,
      preventDefault: () => {},
    });
  });
  canvas.addEventListener("touchmove", (e) => {
    const touch = e.touches[0];
    handleMouseMove({ clientX: touch.clientX, clientY: touch.clientY });
  });
  canvas.addEventListener("touchend", (e) => {
    const touch = e.changedTouches[0];
    handleMouseUp({ clientX: touch.clientX, clientY: touch.clientY });
  });

  // === MODEL SYNC ===
  chartImage.onload = function () {
    imageLoaded = true;
    draw();
  };
  chartImage.src = model.get("chart_base64");

  model.on("change:mode", () => {
    currentMode = model.get("mode");
    updateModeButtons();
    isSelecting = false;
    isDragging = false;
    lassoPath = [];
    selectionStart = null;
    dragStart = null;
    draw();
  });
  model.on("change:selection", draw);
  model.on("change:has_selection", draw);
  model.on("change:chart_base64", () => {
    chartImage.src = model.get("chart_base64");
  });
  model.on("change:selection_color", draw);
  model.on("change:selection_opacity", draw);

  // Initial state
  updateModeButtons();
  draw();
}

export default { render };
