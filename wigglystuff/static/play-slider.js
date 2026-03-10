const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';

function render({ model, el }) {
  const width = model.get("width");

  const wrapper = document.createElement("div");
  wrapper.className = "play-slider-wrapper";
  wrapper.style.width = width + "px";

  const btn = document.createElement("button");
  btn.className = "play-slider-btn";
  btn.type = "button";

  const slider = document.createElement("input");
  slider.className = "play-slider-range";
  slider.type = "range";

  const label = document.createElement("span");
  label.className = "play-slider-label";

  wrapper.appendChild(btn);
  wrapper.appendChild(slider);
  wrapper.appendChild(label);
  el.appendChild(wrapper);

  let intervalId = null;
  let localUpdate = false;

  function syncSliderAttrs() {
    const min = model.get("min_value");
    const max = model.get("max_value");
    const step = model.get("step");
    slider.min = min;
    slider.max = max;
    slider.step = step;
  }

  function updateTrackFill() {
    const min = parseFloat(slider.min);
    const max = parseFloat(slider.max);
    const val = parseFloat(slider.value);
    const pct = ((val - min) / (max - min)) * 100;
    const fill = getComputedStyle(wrapper).getPropertyValue("--play-slider-fill").trim();
    const track = getComputedStyle(wrapper).getPropertyValue("--play-slider-track").trim();
    slider.style.background = `linear-gradient(to right, ${fill} ${pct}%, ${track} ${pct}%)`;
  }

  function renderValue() {
    const val = model.get("value");
    slider.value = val;
    label.textContent = val;
    updateTrackFill();
  }

  function renderBtn() {
    btn.innerHTML = model.get("playing") ? PAUSE_ICON : PLAY_ICON;
  }

  function snap(val) {
    const step = model.get("step");
    const min = model.get("min_value");
    return Math.round((val - min) / step) * step + min;
  }

  function tick() {
    const max = model.get("max_value");
    const min = model.get("min_value");
    const step = model.get("step");
    let val = model.get("value") + step;
    val = snap(val);

    if (val > max) {
      if (model.get("loop")) {
        val = min;
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

  // Manual slider input
  slider.addEventListener("input", () => {
    localUpdate = true;
    model.set("value", parseFloat(slider.value));
    model.save_changes();
    updateTrackFill();
  });

  // React to Python-side value changes
  model.on("change:value", () => {
    renderValue();
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
      intervalId = null;
      const ms = model.get("interval_ms");
      intervalId = setInterval(tick, ms);
    }
  });

  // React to bounds/step changes
  model.on("change:min_value", syncSliderAttrs);
  model.on("change:max_value", syncSliderAttrs);
  model.on("change:step", syncSliderAttrs);

  model.on("change:width", () => {
    wrapper.style.width = model.get("width") + "px";
  });

  // Initial render
  syncSliderAttrs();
  renderValue();
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
