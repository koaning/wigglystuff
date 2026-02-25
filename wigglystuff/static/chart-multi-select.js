const CLASS_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"];

function render({ model, el }) {
  // === DOM SETUP ===
  const container = document.createElement("div");
  container.className = "chart-multi-select";

  const canvas = document.createElement("canvas");
  canvas.width = model.get("width");
  canvas.height = model.get("height");
  canvas.className = "chart-multi-select__canvas";

  // SVG icons
  const boxIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="2" y="2" width="10" height="10" rx="1"/>
  </svg>`;
  const lassoIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M7 2C4 2 2 4.5 2 7c0 2 1 3.5 3 4M10 11c1.5-1 2-2.5 2-4 0-2.5-2-5-5-5"/>
    <circle cx="5" cy="11" r="1.5" fill="currentColor"/>
  </svg>`;
  const trashIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M3 4h8M5 4V3a1 1 0 011-1h2a1 1 0 011 1v1M4 4v7a1 1 0 001 1h4a1 1 0 001-1V4"/>
  </svg>`;
  const undoIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M3 5l3-3M3 5l3 3M4 5h5a3 3 0 010 6H7"/>
  </svg>`;
  const clearIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M3 3l8 8M11 3l-8 8"/>
  </svg>`;

  // --- Build controls ---
  const controls = document.createElement("div");
  controls.className = "chart-multi-select__controls";

  // Mode buttons
  const availableModes = model.get("modes") || ["box", "lasso"];
  const modeConfig = [
    { mode: "box", icon: boxIcon, label: "Box" },
    { mode: "lasso", icon: lassoIcon, label: "Lasso" },
  ].filter((m) => availableModes.includes(m.mode));

  const modes = modeConfig.map((m) => m.mode);
  const modeButtons = {};

  if (modeConfig.length > 1) {
    modeConfig.forEach(({ mode, icon, label }) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chart-multi-select__mode-btn";
      btn.dataset.mode = mode;
      btn.innerHTML = `<span class="chart-multi-select__icon">${icon}</span><span class="chart-multi-select__label">${label}</span>`;
      btn.title = label;
      btn.addEventListener("click", () => setMode(mode));
      controls.appendChild(btn);
      modeButtons[mode] = btn;
    });

    const sep1 = document.createElement("span");
    sep1.className = "chart-multi-select__separator";
    controls.appendChild(sep1);
  }

  // Class buttons
  const classButtons = [];
  function buildClassButtons() {
    // Remove old
    classButtons.forEach((btn) => btn.remove());
    classButtons.length = 0;

    const nClasses = model.get("n_classes");
    for (let i = 0; i < nClasses; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chart-multi-select__class-btn";
      const color = CLASS_COLORS[i % CLASS_COLORS.length];
      btn.innerHTML = `<span class="chart-multi-select__class-dot" style="background:${color}"></span><span class="chart-multi-select__label">${String.fromCharCode(97 + i)}</span>`;
      btn.title = `Class ${i}`;
      btn.addEventListener("click", () => {
        model.set("active_class", i);
        model.save_changes();
        updateClassButtons();
      });
      classButtons.push(btn);
      // Insert before the action separator (or at end of controls)
      controls.insertBefore(btn, actionSep);
    }
    updateClassButtons();
  }

  // Separator before action buttons
  const actionSep = document.createElement("span");
  actionSep.className = "chart-multi-select__separator";
  controls.appendChild(actionSep);

  // Action buttons
  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "chart-multi-select__action-btn chart-multi-select__action-btn--danger";
  deleteBtn.innerHTML = trashIcon;
  deleteBtn.title = "Delete selected";
  deleteBtn.disabled = true;
  deleteBtn.addEventListener("click", deleteSelected);

  const undoBtn = document.createElement("button");
  undoBtn.type = "button";
  undoBtn.className = "chart-multi-select__action-btn";
  undoBtn.innerHTML = undoIcon;
  undoBtn.title = "Undo last";
  undoBtn.addEventListener("click", undoLast);

  const clearBtn = document.createElement("button");
  clearBtn.type = "button";
  clearBtn.className = "chart-multi-select__action-btn chart-multi-select__action-btn--danger";
  clearBtn.innerHTML = clearIcon;
  clearBtn.title = "Clear all";
  clearBtn.addEventListener("click", clearAll);

  controls.appendChild(deleteBtn);
  controls.appendChild(undoBtn);
  controls.appendChild(clearBtn);

  container.appendChild(controls);
  container.appendChild(canvas);
  el.appendChild(container);

  // === STATE ===
  const ctx = canvas.getContext("2d");
  const chartImage = new Image();
  let imageLoaded = false;
  let currentMode = model.get("mode");

  // Drawing state
  let isSelecting = false;
  let isDragging = false;
  let selectionStart = null;
  let dragStart = null;
  let dragIndex = -1;
  let lassoPath = [];

  // === COORDINATE TRANSFORMS ===
  function pixelToData(pixelX, pixelY) {
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const [left, top, right, bottom] = model.get("axes_pixel_bounds");

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

  // Returns index of the topmost selection containing the point, or -1
  function findSelectionAt(coords) {
    const selections = model.get("selections") || [];
    for (let i = selections.length - 1; i >= 0; i--) {
      if (isPointInSelection(coords, selections[i])) return i;
    }
    return -1;
  }

  function isPointInSelection(coords, sel) {
    if (sel.type === "box") {
      const topLeft = dataToPixel(sel.x_min, sel.y_max);
      const bottomRight = dataToPixel(sel.x_max, sel.y_min);
      return (
        coords.x >= topLeft.x &&
        coords.x <= bottomRight.x &&
        coords.y >= topLeft.y &&
        coords.y <= bottomRight.y
      );
    }
    if (sel.vertices && sel.vertices.length >= 3) {
      const pixelVerts = sel.vertices.map((v) => dataToPixel(v[0], v[1]));
      return pointInPolygon(coords, pixelVerts);
    }
    return false;
  }

  function pointInPolygon(point, vertices) {
    let inside = false;
    for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i++) {
      const xi = vertices[i].x, yi = vertices[i].y;
      const xj = vertices[j].x, yj = vertices[j].y;
      if (
        yi > point.y !== yj > point.y &&
        point.x < ((xj - xi) * (point.y - yi)) / (yj - yi) + xi
      ) {
        inside = !inside;
      }
    }
    return inside;
  }

  // === MODE / CLASS MANAGEMENT ===
  function setMode(mode) {
    currentMode = mode;
    model.set("mode", mode);
    model.save_changes();
    updateModeButtons();
    cancelDrawing();
    draw();
  }

  function updateModeButtons() {
    modes.forEach((mode) => {
      if (modeButtons[mode]) {
        modeButtons[mode].classList.toggle("active", mode === currentMode);
      }
    });
  }

  function updateClassButtons() {
    const active = model.get("active_class");
    classButtons.forEach((btn, i) => {
      const color = CLASS_COLORS[i % CLASS_COLORS.length];
      const isActive = i === active;
      btn.classList.toggle("active", isActive);
      btn.style.borderColor = isActive ? color : "";
      btn.style.background = isActive ? hexToRgba(color, 0.15) : "";
    });
  }

  function updateActionButtons() {
    const selectedIdx = model.get("selected_index");
    deleteBtn.disabled = selectedIdx < 0;
  }

  // === ACTIONS ===
  function deleteSelected() {
    const idx = model.get("selected_index");
    const selections = model.get("selections") || [];
    if (idx < 0 || idx >= selections.length) return;
    const newSelections = selections.filter((_, i) => i !== idx);
    model.set("selections", newSelections);
    model.set("selected_index", -1);
    model.save_changes();
    draw();
  }

  function undoLast() {
    const selections = model.get("selections") || [];
    if (selections.length === 0) return;
    const newSelections = selections.slice(0, -1);
    const selectedIdx = model.get("selected_index");
    model.set("selections", newSelections);
    if (selectedIdx >= newSelections.length) {
      model.set("selected_index", -1);
    }
    model.save_changes();
    draw();
  }

  function clearAll() {
    model.set("selections", []);
    model.set("selected_index", -1);
    model.save_changes();
    cancelDrawing();
    draw();
  }

  function highlightAt(coords) {
    const hitIndex = findSelectionAt(coords);
    if (hitIndex >= 0) {
      model.set("selected_index", hitIndex);
      model.save_changes();
      updateActionButtons();
      draw();
    }
  }

  function cancelDrawing() {
    isSelecting = false;
    isDragging = false;
    lassoPath = [];
    selectionStart = null;
    dragStart = null;
    dragIndex = -1;
  }

  // === EVENT HANDLERS ===
  function getCanvasCoords(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY,
    };
  }

  function handleMouseDown(event) {
    event.preventDefault();
    const coords = getCanvasCoords(event);
    const hitIndex = findSelectionAt(coords);
    const selectedIdx = model.get("selected_index");

    // Click on the already-highlighted selection → drag it
    if (hitIndex >= 0 && hitIndex === selectedIdx) {
      isDragging = true;
      dragStart = coords;
      dragIndex = hitIndex;
      return;
    }

    // Deselect any highlighted selection when clicking elsewhere
    if (selectedIdx >= 0) {
      model.set("selected_index", -1);
      model.save_changes();
      updateActionButtons();
      draw();
    }

    // Start new selection if inside axes (draws on top of existing ones)
    if (!isInsideAxes(coords)) return;

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

    // Dragging a selection
    if (isDragging && dragStart && dragIndex >= 0) {
      const dx = coords.x - dragStart.x;
      const dy = coords.y - dragStart.y;
      moveSelection(dragIndex, dx, dy);
      dragStart = coords;
      return;
    }

    // Cursor feedback — show "move" only on the highlighted selection
    const hitIndex = findSelectionAt(coords);
    const isHighlighted = hitIndex >= 0 && hitIndex === model.get("selected_index");
    canvas.style.cursor = isHighlighted ? "move" : "crosshair";

    // Drawing preview
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
      dragIndex = -1;
      return;
    }

    if (currentMode === "box" && isSelecting) {
      const startData = pixelToData(selectionStart.x, selectionStart.y);
      const endData = pixelToData(coords.x, coords.y);

      const w = Math.abs(endData.x - startData.x);
      const h = Math.abs(endData.y - startData.y);
      if (w > 0.01 || h > 0.01) {
        const sel = {
          type: "box",
          class_id: model.get("active_class"),
          x_min: Math.min(startData.x, endData.x),
          y_min: Math.min(startData.y, endData.y),
          x_max: Math.max(startData.x, endData.x),
          y_max: Math.max(startData.y, endData.y),
        };
        const selections = (model.get("selections") || []).slice();
        selections.push(sel);
        model.set("selections", selections);
        model.set("selected_index", -1);
        model.save_changes();
      } else {
        // Click was too small — treat as a highlight click
        highlightAt(coords);
      }
      isSelecting = false;
      selectionStart = null;
    } else if (currentMode === "lasso" && isSelecting) {
      if (lassoPath.length >= 3) {
        const vertices = lassoPath.map((p) => {
          const d = pixelToData(p.x, p.y);
          return [d.x, d.y];
        });
        const sel = {
          type: "lasso",
          class_id: model.get("active_class"),
          vertices,
        };
        const selections = (model.get("selections") || []).slice();
        selections.push(sel);
        model.set("selections", selections);
        model.set("selected_index", -1);
        model.save_changes();
      } else {
        // Click was too small — treat as a highlight click
        highlightAt(coords);
      }
      isSelecting = false;
      lassoPath = [];
    }

    draw();
  }

  function moveSelection(index, dx, dy) {
    const selections = (model.get("selections") || []).slice();
    if (index < 0 || index >= selections.length) return;

    const [left, top, right, bottom] = model.get("axes_pixel_bounds");
    const [xMin, xMax] = model.get("x_bounds");
    const [yMin, yMax] = model.get("y_bounds");
    const pixelWidth = right - left;
    const pixelHeight = bottom - top;
    const ddx = (dx / pixelWidth) * (xMax - xMin);
    const ddy = -(dy / pixelHeight) * (yMax - yMin);

    const sel = { ...selections[index] };
    if (sel.type === "box") {
      sel.x_min += ddx;
      sel.y_min += ddy;
      sel.x_max += ddx;
      sel.y_max += ddy;
    } else if (sel.vertices) {
      sel.vertices = sel.vertices.map((v) => [v[0] + ddx, v[1] + ddy]);
    }
    selections[index] = sel;
    model.set("selections", selections);
    model.save_changes();
    draw();
  }

  // === DRAWING ===
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (imageLoaded) ctx.drawImage(chartImage, 0, 0);

    const selections = model.get("selections") || [];
    const selectedIdx = model.get("selected_index");
    const opacity = model.get("selection_opacity");
    const strokeWidth = model.get("stroke_width");

    selections.forEach((sel, i) => {
      const color = CLASS_COLORS[sel.class_id % CLASS_COLORS.length];
      const isHighlighted = i === selectedIdx;
      drawSingleSelection(sel, color, opacity, strokeWidth, isHighlighted);
    });
  }

  function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function drawSingleSelection(sel, color, opacity, strokeWidth, isHighlighted) {
    ctx.save();
    ctx.fillStyle = hexToRgba(color, opacity);
    ctx.strokeStyle = color;
    ctx.lineWidth = isHighlighted ? strokeWidth + 2 : strokeWidth;

    if (isHighlighted) {
      ctx.setLineDash([6, 3]);
    }

    if (sel.type === "box") {
      const topLeft = dataToPixel(sel.x_min, sel.y_max);
      const bottomRight = dataToPixel(sel.x_max, sel.y_min);
      const w = bottomRight.x - topLeft.x;
      const h = bottomRight.y - topLeft.y;
      ctx.fillRect(topLeft.x, topLeft.y, w, h);
      ctx.strokeRect(topLeft.x, topLeft.y, w, h);
    } else if (sel.vertices && sel.vertices.length >= 3) {
      ctx.beginPath();
      const first = dataToPixel(sel.vertices[0][0], sel.vertices[0][1]);
      ctx.moveTo(first.x, first.y);
      for (let i = 1; i < sel.vertices.length; i++) {
        const p = dataToPixel(sel.vertices[i][0], sel.vertices[i][1]);
        ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    ctx.restore();
  }

  function drawBoxPreview(start, end) {
    const color = CLASS_COLORS[model.get("active_class") % CLASS_COLORS.length];
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
    const color = CLASS_COLORS[model.get("active_class") % CLASS_COLORS.length];
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
    cancelDrawing();
    draw();
  });
  model.on("change:selections", () => {
    updateActionButtons();
    draw();
  });
  model.on("change:selected_index", () => {
    updateActionButtons();
    draw();
  });
  model.on("change:chart_base64", () => {
    chartImage.src = model.get("chart_base64");
  });
  model.on("change:selection_opacity", draw);
  model.on("change:active_class", updateClassButtons);
  model.on("change:n_classes", buildClassButtons);

  // Initial state
  buildClassButtons();
  updateModeButtons();
  updateActionButtons();
  draw();
}

export default { render };
