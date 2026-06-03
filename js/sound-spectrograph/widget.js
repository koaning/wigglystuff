const REGION_COLORS = ["#06b6d4", "#f97316", "#84cc16", "#ec4899", "#8b5cf6"];

function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "sound-spectrograph";

  const toolbar = document.createElement("div");
  toolbar.className = "sound-spectrograph-toolbar";

  const boxIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <rect x="2" y="2" width="10" height="10" rx="1"/>
  </svg>`;
  const lassoIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M7 2C4 2 2 4.5 2 7c0 2 1 3.5 3 4M10 11c1.5-1 2-2.5 2-4 0-2.5-2-5-5-5"/>
    <circle cx="5" cy="11" r="1.5" fill="currentColor"/>
  </svg>`;
  const playIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="currentColor">
    <path d="M4 2.5v9l7-4.5-7-4.5z"/>
  </svg>`;
  const pauseIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="currentColor">
    <path d="M3.5 2.5h2.5v9h-2.5zM8 2.5h2.5v9h-2.5z"/>
  </svg>`;
  const stopIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="currentColor">
    <path d="M3 3h8v8H3z"/>
  </svg>`;
  const plusIcon = `<svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
    <path d="M7 2v10M2 7h10"/>
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

  const availableModes = model.get("modes") || ["box", "lasso"];
  const modeConfig = [
    { mode: "box", icon: boxIcon, label: "Box" },
    { mode: "lasso", icon: lassoIcon, label: "Lasso" },
  ].filter((item) => availableModes.includes(item.mode));
  const modeButtons = {};

  if (modeConfig.length > 1) {
    modeConfig.forEach(({ mode, icon, label }) => {
      const modeButton = document.createElement("button");
      modeButton.type = "button";
      modeButton.className = "sound-spectrograph-mode-btn";
      modeButton.dataset.mode = mode;
      modeButton.innerHTML = `<span class="sound-spectrograph-icon">${icon}</span><span class="sound-spectrograph-label">${label}</span>`;
      modeButton.title = label;
      modeButton.addEventListener("click", () => setMode(mode));
      toolbar.appendChild(modeButton);
      modeButtons[mode] = modeButton;
    });
    toolbar.appendChild(separator());
  }

  const playButton = actionButton(playIcon, "Play audio or selected regions", "Play");
  const pauseButton = actionButton(pauseIcon, "Pause playback");
  const stopButton = actionButton(stopIcon, "Stop playback");
  const newGroupButton = actionButton(plusIcon, "Create a new region group", "New region");
  const deleteButton = actionButton(trashIcon, "Delete selected");
  const undoButton = actionButton(undoIcon, "Undo latest selection in the active region");
  const clearButton = actionButton(clearIcon, "Clear all selections");
  const status = document.createElement("span");
  status.className = "sound-spectrograph-status";

  toolbar.append(playButton, pauseButton, stopButton, newGroupButton, deleteButton, undoButton, clearButton, status);

  const canvasWrap = document.createElement("div");
  canvasWrap.className = "sound-spectrograph-canvas-wrap";

  const canvas = document.createElement("canvas");
  canvas.className = "sound-spectrograph-canvas";
  canvasWrap.appendChild(canvas);

  const groups = document.createElement("div");
  groups.className = "sound-spectrograph-groups";

  const audio = document.createElement("audio");
  audio.className = "sound-spectrograph-audio";
  audio.controls = false;
  audio.preload = "auto";
  audio.hidden = true;

  root.append(toolbar, canvasWrap, groups, audio);
  el.appendChild(root);

  const ctx = canvas.getContext("2d");
  const image = new Image();
  let imageReady = false;
  let drawing = false;
  let currentMode = normalizeMode(model.get("mode") || "box");
  let draftStart = null;
  let draftPoints = [];
  let playbackFrame = null;
  let seeking = false;
  let lastPlaybackSignature = "";

  function syncCanvasSize() {
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    const ratio = window.devicePixelRatio || 1;
    canvasWrap.style.width = `${width}px`;
    canvas.style.width = "100%";
    canvas.style.height = "auto";
    canvas.width = Math.max(1, Math.round(width * ratio));
    canvas.height = Math.max(1, Math.round(height * ratio));
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    draw();
  }

  function setImage() {
    imageReady = false;
    image.onload = () => {
      imageReady = true;
      draw();
    };
    image.src = model.get("spectrogram_base64") || "";
  }

  function draw() {
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    ctx.clearRect(0, 0, width, height);
    if (imageReady) {
      ctx.drawImage(image, 0, 0, width, height);
    } else {
      ctx.fillStyle = "#111827";
      ctx.fillRect(0, 0, width, height);
    }
    drawSelections();
    drawPlaybackProgress();
    drawDraft();
  }

  function drawPlaybackProgress() {
    if (!hasPlayableAudio()) return;
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    const x = playheadPixel();

    ctx.save();
    ctx.fillStyle = audio.paused ? "rgba(2, 6, 23, 0.34)" : "rgba(2, 6, 23, 0.52)";
    ctx.fillRect(x, 0, width - x, height);

    const gradient = ctx.createLinearGradient(Math.max(0, x - 8), 0, x + 8, 0);
    gradient.addColorStop(0, "rgba(255, 255, 255, 0)");
    gradient.addColorStop(0.5, "rgba(255, 255, 255, 0.92)");
    gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(Math.max(0, x - 8), 0, 16, height);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.96)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
    ctx.fillStyle = "rgba(255, 255, 255, 0.96)";
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x - 5, 8);
    ctx.lineTo(x + 5, 8);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x, height);
    ctx.lineTo(x - 5, height - 8);
    ctx.lineTo(x + 5, height - 8);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawSelections() {
    const selections = model.get("selections") || [];
    const selectedIndex = model.get("selected_index") ?? -1;
    const opacity = model.get("selection_opacity") ?? 0.28;
    const strokeWidth = model.get("stroke_width") ?? 2;
    const selectionGroups = getGroups();

    selections.forEach((selection, index) => {
      const group = groupForSelection(selection, selectionGroups);
      if (group && group.enabled === false) return;
      const color = group?.color || selection.color || REGION_COLORS[index % REGION_COLORS.length];
      const lineWidth = index === selectedIndex ? strokeWidth + 1 : strokeWidth;
      if (selection.type === "box") {
        drawBox(selection, color, opacity, lineWidth);
      } else {
        const points = dataVerticesToPixels(selection.vertices || []);
        if (points.length < 3) return;
        drawPolygon(points, color, opacity, lineWidth);
      }
    });
  }

  function drawDraft() {
    if (!drawing) return;
    if (currentMode === "box") {
      if (!draftStart || draftPoints.length < 1) return;
      drawBoxPreview(draftStart, draftPoints[draftPoints.length - 1]);
      return;
    }
    if (draftPoints.length < 2) return;
    ctx.save();
    ctx.strokeStyle = "#f8fafc";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(draftPoints[0].x, draftPoints[0].y);
    for (const point of draftPoints.slice(1)) {
      ctx.lineTo(point.x, point.y);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawBox(selection, color, opacity, lineWidth) {
    const topLeft = dataToPixel([selection.x_min, selection.y_max]);
    const bottomRight = dataToPixel([selection.x_max, selection.y_min]);
    const width = bottomRight.x - topLeft.x;
    const height = bottomRight.y - topLeft.y;
    ctx.save();
    ctx.fillStyle = withAlpha(color, opacity);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.fillRect(topLeft.x, topLeft.y, width, height);
    ctx.strokeRect(topLeft.x, topLeft.y, width, height);
    ctx.restore();
  }

  function drawBoxPreview(start, end) {
    const selectionGroups = getGroups();
    const group = selectionGroups[activeGroupIndex(selectionGroups)];
    const color = group?.color || REGION_COLORS[0];
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    ctx.strokeRect(start.x, start.y, end.x - start.x, end.y - start.y);
    ctx.fillStyle = withAlpha(color, 0.12);
    ctx.fillRect(start.x, start.y, end.x - start.x, end.y - start.y);
    ctx.restore();
  }

  function drawPolygon(points, color, opacity, lineWidth) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (const point of points.slice(1)) {
      ctx.lineTo(point.x, point.y);
    }
    ctx.closePath();
    ctx.fillStyle = withAlpha(color, opacity);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function updateGroups() {
    ensureGroups();
    const selectionGroups = getGroups();
    const selections = model.get("selections") || [];
    const activeIndex = activeGroupIndex(selectionGroups);
    groups.replaceChildren();
    selectionGroups.forEach((group, index) => {
      const row = document.createElement("div");
      row.className = "sound-spectrograph-group";
      row.classList.toggle("is-active", index === activeIndex);
      row.style.setProperty("--region-color", group.color || REGION_COLORS[index % REGION_COLORS.length]);

      const selectionCount = selections.filter((selection) => selectionBelongsToGroup(selection, group, selectionGroups)).length;
      const groupButton = button(`${group.name || `Region ${index + 1}`} (${selectionCount})`, `Use ${group.name || `Region ${index + 1}`}`);
      groupButton.classList.add("sound-spectrograph-group-name");
      groupButton.classList.toggle("is-active", index === activeIndex);
      groupButton.addEventListener("click", () => selectGroup(index));

      const toggleButton = button(group.enabled === false ? "Off" : "On", `${group.enabled === false ? "Enable" : "Disable"} ${group.name || `Region ${index + 1}`}`);
      toggleButton.classList.add("sound-spectrograph-toggle");
      toggleButton.classList.toggle("is-off", group.enabled === false);
      toggleButton.addEventListener("click", () => toggleGroup(index));

      row.append(groupButton, toggleButton);
      groups.appendChild(row);
    });
  }

  function updateStatus() {
    const error = model.get("playback_error") || "";
    if (error) {
      status.textContent = error;
      status.classList.add("is-error");
      return;
    }
    status.classList.remove("is-error");
    if (hasPlayableAudio()) {
      const state = model.get("is_playing") ? "Playing" : "Paused";
      status.textContent = `${state} ${formatTime(playheadTime())} / ${formatTime(model.get("duration") || audio.duration)}`;
    } else {
      const selectionGroups = getGroups();
      const enabledSelections = (model.get("selections") || []).filter((selection) => {
        const group = groupForSelection(selection, selectionGroups);
        return !group || group.enabled !== false;
      }).length;
      status.textContent = `${selectionGroups.length} ${selectionGroups.length === 1 ? "region" : "regions"}, ${enabledSelections} active ${enabledSelections === 1 ? "selection" : "selections"}`;
    }
  }

  function addSelection(points) {
    if (points.length < 3) return;
    const selectionGroups = ensureGroups();
    const groupIndex = activeGroupIndex(selectionGroups);
    const group = selectionGroups[groupIndex];
    const selections = [...(model.get("selections") || [])];
    const index = selections.length;
    selections.push({
      id: `${Date.now()}-${index}`,
      type: "lasso",
      group_id: group.id,
      color: group.color || REGION_COLORS[groupIndex % REGION_COLORS.length],
      vertices: points.map(pixelToData),
    });
    model.set("selections", selections);
    model.set("selected_index", selections.length - 1);
    model.set("active_group_index", groupIndex);
    model.set("playback_error", "");
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function addBoxSelection(start, end) {
    if (!start || !end || (Math.abs(end.x - start.x) < 3 && Math.abs(end.y - start.y) < 3)) return;
    const selectionGroups = ensureGroups();
    const groupIndex = activeGroupIndex(selectionGroups);
    const group = selectionGroups[groupIndex];
    const startData = pixelToData(start);
    const endData = pixelToData(end);
    const selections = [...(model.get("selections") || [])];
    const index = selections.length;
    selections.push({
      id: `${Date.now()}-${index}`,
      type: "box",
      group_id: group.id,
      color: group.color || REGION_COLORS[groupIndex % REGION_COLORS.length],
      x_min: Math.min(startData[0], endData[0]),
      x_max: Math.max(startData[0], endData[0]),
      y_min: Math.min(startData[1], endData[1]),
      y_max: Math.max(startData[1], endData[1]),
    });
    model.set("selections", selections);
    model.set("selected_index", selections.length - 1);
    model.set("active_group_index", groupIndex);
    model.set("playback_error", "");
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function deleteSelectedSelection() {
    const selections = [...(model.get("selections") || [])];
    const selectedIndex = model.get("selected_index") ?? -1;
    if (selectedIndex < 0 || selectedIndex >= selections.length) return;
    selections.splice(selectedIndex, 1);
    model.set("selections", selections);
    model.set("selected_index", -1);
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function undoActiveGroupSelection() {
    const selectionGroups = getGroups();
    const group = selectionGroups[activeGroupIndex(selectionGroups)];
    const selections = [...(model.get("selections") || [])];
    let selectedIndex = model.get("selected_index") ?? -1;
    if (selectedIndex < 0 || selectedIndex >= selections.length || (group && !selectionBelongsToGroup(selections[selectedIndex], group, selectionGroups))) {
      selectedIndex = findLastSelectionIndexForGroup(selections, group, selectionGroups);
    }
    if (selectedIndex < 0 || selectedIndex >= selections.length) return;
    selections.splice(selectedIndex, 1);
    model.set("selections", selections);
    model.set("selected_index", group ? findLastSelectionIndexForGroup(selections, group, selectionGroups) : Math.min(selectedIndex, selections.length - 1));
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function clearSelections() {
    model.set("selections", []);
    model.set("selected_index", -1);
    model.set("playback_error", "");
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function addGroup() {
    const selectionGroups = [...getGroups()].map((group) => ({ ...group }));
    const index = selectionGroups.length;
    selectionGroups.push({
      id: `region-${Date.now()}-${index + 1}`,
      name: `Region ${index + 1}`,
      color: REGION_COLORS[index % REGION_COLORS.length],
      enabled: true,
    });
    model.set("selection_groups", selectionGroups);
    model.set("active_group_index", index);
    model.set("selected_index", -1);
    model.set("playback_error", "");
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function selectGroup(index) {
    const selectionGroups = getGroups();
    const group = selectionGroups[index];
    if (!group) return;
    const selections = model.get("selections") || [];
    model.set("active_group_index", index);
    model.set("selected_index", findLastSelectionIndexForGroup(selections, group, selectionGroups));
    model.save_changes();
    updateGroups();
    draw();
  }

  function toggleGroup(index) {
    const selectionGroups = getGroups().map((group) => ({ ...group }));
    if (!selectionGroups[index]) return;
    selectionGroups[index].enabled = selectionGroups[index].enabled === false;
    model.set("selection_groups", selectionGroups);
    model.set("playback_error", "");
    model.save_changes();
    updateGroups();
    updateStatus();
    draw();
  }

  function requestOrResumePlayback() {
    if (hasPlayableAudio() && lastPlaybackSignature === playbackSignature()) {
      if (audio.ended || audio.currentTime >= audio.duration) {
        audio.currentTime = 0;
      }
      playAudioFromCurrentTime();
      return;
    }
    requestPlayback();
  }

  function requestPlayback() {
    audio.pause();
    audio.removeAttribute("src");
    audio.load();
    lastPlaybackSignature = "";
    stopPlaybackIndicator();
    model.set("is_playing", false);
    model.set("selected_audio_base64", "");
    model.save_changes();
    window.setTimeout(() => {
      model.set("play_request_id", (model.get("play_request_id") || 0) + 1);
      model.save_changes();
    }, 0);
    status.textContent = "Preparing audio";
    status.classList.remove("is-error");
  }

  function setMode(mode) {
    currentMode = normalizeMode(mode);
    model.set("mode", currentMode);
    model.save_changes();
    cancelDrawing();
    updateModeButtons();
    draw();
  }

  function startPlaybackIndicator() {
    if (playbackFrame !== null) return;
    const tick = () => {
      playbackFrame = null;
      draw();
      updateStatus();
      if (!audio.paused && !audio.ended) {
        playbackFrame = requestAnimationFrame(tick);
      }
    };
    playbackFrame = requestAnimationFrame(tick);
  }

  function stopPlaybackIndicator() {
    if (playbackFrame === null) return;
    cancelAnimationFrame(playbackFrame);
    playbackFrame = null;
  }

  function pausePlayback() {
    if (!audio.src) return;
    audio.pause();
    updateStatus();
    draw();
  }

  function stopPlayback() {
    if (!audio.src) return;
    audio.pause();
    audio.currentTime = 0;
    model.set("is_playing", false);
    model.save_changes();
    stopPlaybackIndicator();
    updateStatus();
    draw();
  }

  function updateModeButtons() {
    Object.entries(modeButtons).forEach(([mode, modeButton]) => {
      modeButton.classList.toggle("active", mode === currentMode);
    });
  }

  function normalizeMode(mode) {
    if (modeConfig.some((item) => item.mode === mode)) return mode;
    return modeConfig[0]?.mode || "box";
  }

  function cancelDrawing() {
    drawing = false;
    draftStart = null;
    draftPoints = [];
  }

  function playSelectedAudio() {
    const source = model.get("selected_audio_base64") || "";
    if (!source) return;
    audio.src = source;
    audio.currentTime = 0;
    lastPlaybackSignature = playbackSignature();
    playAudioFromCurrentTime();
  }

  function playAudioFromCurrentTime() {
    const playPromise = audio.play();
    if (playPromise) {
      playPromise.catch(() => {
        status.textContent = "Playback blocked by browser";
        status.classList.add("is-error");
      });
    }
  }

  function hasPlayableAudio() {
    return Boolean(audio.src) && Number.isFinite(audio.duration) && audio.duration > 0;
  }

  function getCanvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    const rectWidth = rect.width || width;
    const rectHeight = rect.height || height;
    return {
      x: clamp(((event.clientX - rect.left) / rectWidth) * width, 0, width),
      y: clamp(((event.clientY - rect.top) / rectHeight) * height, 0, height),
    };
  }

  function pixelToData(point) {
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    const [minTime, maxTime] = model.get("time_bounds") || [0, 1];
    const [minFrequency, maxFrequency] = model.get("frequency_bounds") || [0, 1];
    const time = minTime + (point.x / width) * (maxTime - minTime);
    let frequency;
    if (model.get("frequency_scale") === "log") {
      const minLog = Math.log10(Math.max(minFrequency, 1));
      const maxLog = Math.log10(Math.max(maxFrequency, 1));
      frequency = 10 ** (maxLog - (point.y / height) * (maxLog - minLog));
    } else {
      frequency = maxFrequency - (point.y / height) * (maxFrequency - minFrequency);
    }
    return [time, frequency];
  }

  function dataToPixel(vertex) {
    const width = model.get("width") || 700;
    const height = model.get("height") || 420;
    const [minTime, maxTime] = model.get("time_bounds") || [0, 1];
    const [minFrequency, maxFrequency] = model.get("frequency_bounds") || [0, 1];
    const x = ((vertex[0] - minTime) / (maxTime - minTime || 1)) * width;
    let y;
    if (model.get("frequency_scale") === "log") {
      const minLog = Math.log10(Math.max(minFrequency, 1));
      const maxLog = Math.log10(Math.max(maxFrequency, 1));
      y = ((maxLog - Math.log10(Math.max(vertex[1], 1))) / (maxLog - minLog || 1)) * height;
    } else {
      y = ((maxFrequency - vertex[1]) / (maxFrequency - minFrequency || 1)) * height;
    }
    return { x, y };
  }

  function dataVerticesToPixels(vertices) {
    return vertices.map(dataToPixel);
  }

  function timeToPixel(time) {
    const width = model.get("width") || 700;
    const [minTime, maxTime] = model.get("time_bounds") || [0, 1];
    return ((time - minTime) / (maxTime - minTime || 1)) * width;
  }

  function pixelToTime(x) {
    const width = model.get("width") || 700;
    const [minTime, maxTime] = model.get("time_bounds") || [0, 1];
    return minTime + (clamp(x, 0, width) / width) * (maxTime - minTime);
  }

  function playheadPixel() {
    const width = model.get("width") || 700;
    return clamp(timeToPixel(playheadTime()), 0, width);
  }

  function playheadTime() {
    if (!hasPlayableAudio()) return 0;
    const [startTime, endTime] = playbackTimeBounds();
    const progress = clamp(audio.currentTime / audio.duration, 0, 1);
    return startTime + progress * (endTime - startTime);
  }

  function seekToPoint(point) {
    if (!hasPlayableAudio()) return;
    const [startTime, endTime] = playbackTimeBounds();
    const time = clamp(pixelToTime(point.x), startTime, endTime);
    const progress = (time - startTime) / (endTime - startTime || 1);
    audio.currentTime = clamp(progress * audio.duration, 0, audio.duration);
    updateStatus();
    draw();
  }

  function isNearPlayhead(point) {
    return hasPlayableAudio() && Math.abs(point.x - playheadPixel()) <= 12;
  }

  function playbackSignature() {
    return JSON.stringify({
      selections: model.get("selections") || [],
      selection_groups: model.get("selection_groups") || [],
      duration: model.get("duration") || 0,
    });
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds)) return "0:00";
    const total = Math.max(0, Math.floor(seconds));
    const minutes = Math.floor(total / 60);
    const remainder = String(total % 60).padStart(2, "0");
    return `${minutes}:${remainder}`;
  }

  function playbackTimeBounds() {
    const [minTime, maxTime] = model.get("time_bounds") || [0, 1];
    const selectionGroups = getGroups();
    const selectedTimes = [];
    (model.get("selections") || []).forEach((selection) => {
      const group = groupForSelection(selection, selectionGroups);
      if (group && group.enabled === false) return;
      if (selection.type === "box") {
        selectedTimes.push(selection.x_min, selection.x_max);
      } else {
        (selection.vertices || []).forEach((vertex) => selectedTimes.push(vertex[0]));
      }
    });
    if (!selectedTimes.length) return [minTime, maxTime];
    return [Math.min(...selectedTimes), Math.max(...selectedTimes)];
  }

  function getGroups() {
    const selectionGroups = model.get("selection_groups") || [];
    return selectionGroups.length ? selectionGroups : [defaultGroup()];
  }

  function ensureGroups() {
    const selectionGroups = model.get("selection_groups") || [];
    if (selectionGroups.length) return selectionGroups;
    const groups = [defaultGroup()];
    model.set("selection_groups", groups);
    model.set("active_group_index", 0);
    model.save_changes();
    return groups;
  }

  function activeGroupIndex(selectionGroups = getGroups()) {
    const index = model.get("active_group_index") ?? 0;
    if (index < 0 || index >= selectionGroups.length) return 0;
    return index;
  }

  function groupForSelection(selection, selectionGroups = getGroups()) {
    if (!selectionGroups.length) return null;
    const groupId = selection?.group_id ?? selectionGroups[0].id;
    return selectionGroups.find((group) => String(group.id) === String(groupId)) || selectionGroups[0];
  }

  function selectionBelongsToGroup(selection, group, selectionGroups = getGroups()) {
    if (!selection || !group) return false;
    const selectionGroup = groupForSelection(selection, selectionGroups);
    return Boolean(selectionGroup && String(selectionGroup.id) === String(group.id));
  }

  function findLastSelectionIndexForGroup(selections, group, selectionGroups = getGroups()) {
    if (!group) return -1;
    for (let index = selections.length - 1; index >= 0; index -= 1) {
      if (selectionBelongsToGroup(selections[index], group, selectionGroups)) return index;
    }
    return -1;
  }

  canvas.addEventListener("pointerdown", (event) => {
    canvas.setPointerCapture(event.pointerId);
    const point = getCanvasPoint(event);
    if (isNearPlayhead(point)) {
      seeking = true;
      seekToPoint(point);
      canvas.style.cursor = "ew-resize";
      return;
    }
    drawing = true;
    draftStart = currentMode === "box" ? point : null;
    draftPoints = [point];
    draw();
  });

  canvas.addEventListener("pointermove", (event) => {
    const point = getCanvasPoint(event);
    if (seeking) {
      seekToPoint(point);
      return;
    }
    if (!drawing) return;
    if (currentMode === "box") {
      draftPoints = [point];
      draw();
      return;
    }
    const previous = draftPoints[draftPoints.length - 1];
    if (!previous || distance(previous, point) >= 2) {
      draftPoints.push(point);
      draw();
    }
  });

  canvas.addEventListener("pointerup", (event) => {
    if (seeking) {
      seeking = false;
      seekToPoint(getCanvasPoint(event));
      canvas.style.cursor = "crosshair";
      return;
    }
    if (!drawing) return;
    const point = getCanvasPoint(event);
    if (currentMode === "box") {
      const start = draftStart;
      cancelDrawing();
      addBoxSelection(start, point);
      return;
    }
    drawing = false;
    draftPoints.push(point);
    const points = simplifyDraft(draftPoints);
    draftPoints = [];
    addSelection(points);
  });

  canvas.addEventListener("pointercancel", () => {
    seeking = false;
    cancelDrawing();
    canvas.style.cursor = "crosshair";
    draw();
  });

  canvas.addEventListener("pointerleave", () => {
    if (!drawing && !seeking) canvas.style.cursor = "crosshair";
  });

  canvas.addEventListener("pointermove", (event) => {
    if (drawing || seeking) return;
    canvas.style.cursor = isNearPlayhead(getCanvasPoint(event)) ? "ew-resize" : "crosshair";
  });

  playButton.addEventListener("click", requestOrResumePlayback);
  pauseButton.addEventListener("click", pausePlayback);
  stopButton.addEventListener("click", stopPlayback);
  newGroupButton.addEventListener("click", addGroup);
  deleteButton.addEventListener("click", deleteSelectedSelection);
  undoButton.addEventListener("click", undoActiveGroupSelection);
  clearButton.addEventListener("click", clearSelections);
  audio.addEventListener("play", () => {
    model.set("is_playing", true);
    model.save_changes();
    startPlaybackIndicator();
    updateStatus();
  });
  audio.addEventListener("loadedmetadata", () => {
    updateStatus();
    draw();
  });
  audio.addEventListener("timeupdate", () => {
    updateStatus();
    draw();
  });
  audio.addEventListener("pause", () => {
    model.set("is_playing", false);
    model.save_changes();
    stopPlaybackIndicator();
    updateStatus();
    draw();
  });
  audio.addEventListener("ended", () => {
    model.set("is_playing", false);
    model.save_changes();
    stopPlaybackIndicator();
    updateStatus();
    draw();
  });

  model.on("change:spectrogram_base64", setImage);
  model.on("change:selected_audio_base64", playSelectedAudio);
  model.on("change:mode", () => {
    currentMode = normalizeMode(model.get("mode") || "box");
    cancelDrawing();
    updateModeButtons();
    draw();
  });
  model.on("change:selections", () => {
    updateGroups();
    updateStatus();
    draw();
  });
  model.on("change:selected_index", () => {
    updateGroups();
    draw();
  });
  model.on("change:selection_groups", () => {
    updateGroups();
    updateStatus();
    draw();
  });
  model.on("change:active_group_index", () => {
    updateGroups();
    draw();
  });
  model.on("change:playback_error", updateStatus);
  model.on("change:is_playing", updateStatus);
  model.on("change:width", syncCanvasSize);
  model.on("change:height", syncCanvasSize);

  syncCanvasSize();
  setImage();
  updateModeButtons();
  updateGroups();
  updateStatus();
}

function defaultGroup() {
  return { id: "region-1", name: "Region 1", color: REGION_COLORS[0], enabled: true };
}

function button(label, title) {
  const element = document.createElement("button");
  element.type = "button";
  element.className = "sound-spectrograph-button";
  element.textContent = label;
  element.title = title;
  return element;
}

function actionButton(icon, title, label = "") {
  const element = document.createElement("button");
  element.type = "button";
  element.className = label
    ? "sound-spectrograph-action-btn sound-spectrograph-action-btn--label"
    : "sound-spectrograph-action-btn";
  element.innerHTML = `<span class="sound-spectrograph-icon">${icon}</span>${label ? `<span class="sound-spectrograph-label">${label}</span>` : ""}`;
  element.title = title;
  return element;
}

function separator() {
  const element = document.createElement("span");
  element.className = "sound-spectrograph-separator";
  return element;
}

function withAlpha(hex, alpha) {
  const clean = hex.replace("#", "");
  const red = parseInt(clean.slice(0, 2), 16);
  const green = parseInt(clean.slice(2, 4), 16);
  const blue = parseInt(clean.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function simplifyDraft(points) {
  if (points.length <= 160) return points;
  const step = Math.ceil(points.length / 160);
  return points.filter((_, index) => index % step === 0 || index === points.length - 1);
}

export default { render };