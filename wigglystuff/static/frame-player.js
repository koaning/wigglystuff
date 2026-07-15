const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';

function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.className = "frame-player-wrapper";

  const image = document.createElement("img");
  image.className = "frame-player-image";

  const controls = document.createElement("div");
  controls.className = "frame-player-controls";

  const btn = document.createElement("button");
  btn.className = "frame-player-btn";
  btn.type = "button";

  const slider = document.createElement("input");
  slider.className = "frame-player-range";
  slider.type = "range";
  slider.step = "1";
  slider.min = "0";

  const label = document.createElement("span");
  label.className = "frame-player-index";

  controls.appendChild(btn);
  controls.appendChild(slider);
  controls.appendChild(label);
  wrapper.appendChild(image);
  wrapper.appendChild(controls);
  el.appendChild(wrapper);

  let intervalId = null;
  // Local frame index — the single source of truth for what's displayed.
  // Playback is purely client-side; the widget never writes state back to the
  // kernel, so there is no comm round-trip per frame and nothing to echo.
  let cur = 0;

  function maxIndex() {
    return Math.max(0, model.get("frames").length - 1);
  }

  function clampIndex(i) {
    return Math.max(0, Math.min(i, maxIndex()));
  }

  function applyWidth() {
    const w = model.get("width");
    if (w > 0) {
      wrapper.style.width = w + "px";
      image.style.width = w + "px";
    } else {
      wrapper.style.width = "";
      image.style.width = "";
    }
  }

  function updateTrackFill() {
    const min = parseFloat(slider.min);
    const max = parseFloat(slider.max);
    const val = parseFloat(slider.value);
    const pct = max > min ? ((val - min) / (max - min)) * 100 : 0;
    const fill = getComputedStyle(wrapper).getPropertyValue("--frame-player-fill").trim();
    const track = getComputedStyle(wrapper).getPropertyValue("--frame-player-track").trim();
    slider.style.background = `linear-gradient(to right, ${fill} ${pct}%, ${track} ${pct}%)`;
  }

  function syncSliderAttrs() {
    slider.max = maxIndex();
  }

  function renderFrame() {
    const frames = model.get("frames");
    const idx = clampIndex(cur);
    if (frames.length > 0) {
      image.src = frames[idx];
    } else {
      image.removeAttribute("src");
    }
    slider.value = idx;
    label.style.display = model.get("show_index") ? "" : "none";
    label.textContent = `${idx + 1} / ${frames.length}`;
    updateTrackFill();
  }

  function renderBtn() {
    btn.innerHTML = intervalId !== null ? PAUSE_ICON : PLAY_ICON;
  }

  function tick() {
    const max = maxIndex();
    let next = cur + 1;

    if (next > max) {
      if (model.get("loop")) {
        next = 0;
      } else {
        stopPlaying();
        return;
      }
    }

    cur = next;
    renderFrame();
  }

  function startPlaying() {
    if (intervalId !== null) return;
    intervalId = setInterval(tick, model.get("interval_ms"));
    renderBtn();
  }

  function stopPlaying() {
    if (intervalId === null) return;
    clearInterval(intervalId);
    intervalId = null;
    renderBtn();
  }

  // Button click toggles play/pause
  btn.addEventListener("click", () => {
    if (intervalId !== null) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

  // Manual scrubbing — moves the local playhead; playback (if running)
  // continues from the new position.
  slider.addEventListener("input", () => {
    cur = clampIndex(parseInt(slider.value, 10));
    renderFrame();
  });

  // Python can jump the frame by setting `value` (Python -> JS control).
  model.on("change:value", () => {
    cur = clampIndex(model.get("value"));
    renderFrame();
  });

  // Python can start/stop playback by setting `playing` (Python -> JS control).
  model.on("change:playing", () => {
    if (model.get("playing")) {
      startPlaying();
    } else {
      stopPlaying();
    }
  });

  // React to interval_ms change while playing
  model.on("change:interval_ms", () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = setInterval(tick, model.get("interval_ms"));
    }
  });

  // React to a new frame sequence
  model.on("change:frames", () => {
    syncSliderAttrs();
    cur = clampIndex(cur);
    renderFrame();
  });

  model.on("change:show_index", renderFrame);
  model.on("change:width", applyWidth);

  // Initial render
  applyWidth();
  syncSliderAttrs();
  cur = clampIndex(model.get("value"));
  renderFrame();
  if (model.get("playing")) startPlaying();
  renderBtn();

  // Cleanup
  return () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };
}

export default { render };
