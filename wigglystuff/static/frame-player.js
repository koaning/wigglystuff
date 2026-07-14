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
  let localUpdate = false;

  function maxIndex() {
    return Math.max(0, model.get("frames").length - 1);
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
    const idx = Math.max(0, Math.min(model.get("value"), maxIndex()));
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
    btn.innerHTML = model.get("playing") ? PAUSE_ICON : PLAY_ICON;
  }

  function tick() {
    const max = maxIndex();
    let val = model.get("value") + 1;

    if (val > max) {
      if (model.get("loop")) {
        val = 0;
      } else {
        val = max;
        stopPlaying();
      }
    }

    localUpdate = true;
    model.set("value", val);
    model.save_changes();
  }

  function startPlaying() {
    if (intervalId !== null) return;
    const ms = model.get("interval_ms");
    intervalId = setInterval(tick, ms);
    localUpdate = true;
    model.set("playing", true);
    model.save_changes();
    renderBtn();
  }

  function stopPlaying() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
    localUpdate = true;
    model.set("playing", false);
    model.save_changes();
    renderBtn();
  }

  // Button click toggles play/pause
  btn.addEventListener("click", () => {
    if (model.get("playing")) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

  // Manual scrubbing
  slider.addEventListener("input", () => {
    localUpdate = true;
    model.set("value", parseInt(slider.value, 10));
    model.save_changes();
    renderFrame();
  });

  // React to Python-side value changes
  model.on("change:value", () => {
    renderFrame();
    if (!localUpdate) {
      model.save_changes();
    }
    localUpdate = false;
  });

  // React to Python toggling playing
  model.on("change:playing", () => {
    const playing = model.get("playing");
    if (playing && intervalId === null) {
      startPlaying();
    } else if (!playing && intervalId !== null) {
      stopPlaying();
    }
    renderBtn();
    localUpdate = false;
  });

  // React to interval_ms change while playing
  model.on("change:interval_ms", () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      const ms = model.get("interval_ms");
      intervalId = setInterval(tick, ms);
    }
  });

  // React to a new frame sequence
  model.on("change:frames", () => {
    syncSliderAttrs();
    renderFrame();
  });

  model.on("change:show_index", renderFrame);
  model.on("change:width", applyWidth);

  // Initial render
  applyWidth();
  syncSliderAttrs();
  renderFrame();
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
