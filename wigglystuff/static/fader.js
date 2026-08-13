const SVG_NS = "http://www.w3.org/2000/svg";

// Shared across all faders on the page so we only request access once.
let _midiAccessPromise = null;
function getMidiAccess() {
  if (!navigator.requestMIDIAccess) return Promise.resolve(null);
  if (!_midiAccessPromise) _midiAccessPromise = navigator.requestMIDIAccess();
  return _midiAccessPromise;
}

function getPrecision(step) {
  const s = String(step);
  const dot = s.indexOf(".");
  return dot === -1 ? 0 : s.length - dot - 1;
}

function snap(value, min, max, step) {
  const clamped = Math.max(min, Math.min(max, value));
  if (!step) return clamped;
  const snapped = min + Math.round((clamped - min) / step) * step;
  return Math.max(min, Math.min(max, snapped));
}

function formatValue(value, step) {
  return value.toFixed(getPrecision(step));
}

function nearestStep(value, steps) {
  let best = steps[0];
  let bestDist = Math.abs(value - steps[0]);
  for (const s of steps) {
    const d = Math.abs(value - s);
    if (d < bestDist) {
      bestDist = d;
      best = s;
    }
  }
  return best;
}

const SLOT_W = 6;
const TICK_LEN = 7;
const ACROSS = 36; // cap size perpendicular to the track (the long grip edge)
const ALONG = 14; // cap size along the track

function render({ model, el }) {
  el.innerHTML = "";

  const wrapper = document.createElement("div");
  wrapper.className = "fader-wrapper";

  const title = document.createElement("div");
  title.className = "fader-title";
  wrapper.appendChild(title);

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "fader-svg");

  const slot = document.createElementNS(SVG_NS, "line");
  slot.setAttribute("class", "fader-track");
  svg.appendChild(slot);

  const fill = document.createElementNS(SVG_NS, "line");
  fill.setAttribute("class", "fader-fill");
  svg.appendChild(fill);

  const ticksGroup = document.createElementNS(SVG_NS, "g");
  ticksGroup.setAttribute("class", "fader-ticks");
  svg.appendChild(ticksGroup);

  const cap = document.createElementNS(SVG_NS, "rect");
  cap.setAttribute("class", "fader-cap");
  cap.setAttribute("rx", "3");
  svg.appendChild(cap);

  const groove = document.createElementNS(SVG_NS, "line");
  groove.setAttribute("class", "fader-groove");
  svg.appendChild(groove);

  wrapper.appendChild(svg);

  const valueLabel = document.createElement("div");
  valueLabel.className = "fader-value";
  wrapper.appendChild(valueLabel);

  const midiBtn = document.createElement("button");
  midiBtn.className = "fader-midi-btn";
  midiBtn.type = "button";
  wrapper.appendChild(midiBtn);

  el.appendChild(wrapper);

  let dragging = false;
  let geom = null;

  function valueFraction() {
    const min = model.get("min_value");
    const max = model.get("max_value");
    return (model.get("value") - min) / (max - min);
  }

  function drawTicks(vertical, g) {
    ticksGroup.innerHTML = "";
    const ticks = model.get("ticks") || [];
    const min = model.get("min_value");
    const max = model.get("max_value");
    const span = max - min;
    if (span === 0) return;
    for (const t of ticks) {
      const f = (t.value - min) / span;
      if (f < -1e-6 || f > 1 + 1e-6) continue;
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("class", "fader-tick");
      let lx, ly, anchor, baseline;
      if (vertical) {
        const y = g.end - f * g.len;
        line.setAttribute("x1", g.tick1);
        line.setAttribute("y1", y);
        line.setAttribute("x2", g.tick2);
        line.setAttribute("y2", y);
        lx = g.labelPos;
        ly = y;
        anchor = "start";
        baseline = "middle";
      } else {
        const x = g.start + f * g.len;
        line.setAttribute("x1", x);
        line.setAttribute("y1", g.tick1);
        line.setAttribute("x2", x);
        line.setAttribute("y2", g.tick2);
        lx = x;
        ly = g.labelPos;
        anchor = "middle";
        baseline = "hanging";
      }
      ticksGroup.appendChild(line);
      if (t.label) {
        const text = document.createElementNS(SVG_NS, "text");
        text.setAttribute("class", "fader-tick-label");
        text.setAttribute("x", lx);
        text.setAttribute("y", ly);
        text.setAttribute("text-anchor", anchor);
        text.setAttribute("dominant-baseline", baseline);
        text.textContent = t.label;
        ticksGroup.appendChild(text);
      }
    }
  }

  function updateGeometry() {
    const len = model.get("length");
    const vertical = model.get("orientation") !== "horizontal";
    const ticks = model.get("ticks") || [];
    const hasLabels = ticks.some((t) => t.label);
    const f = valueFraction();

    if (vertical) {
      const trackX = ACROSS / 2 + 2;
      const top = ALONG / 2 + 4;
      const end = top + len; // bottom == min
      const tick1 = trackX + SLOT_W / 2 + 1;
      const tick2 = tick1 + TICK_LEN;
      const labelPos = tick2 + 3;
      // Include the cap's right edge so it isn't clipped when there are no labels.
      const capRight = trackX + ACROSS / 2 + 2;
      const svgW = Math.max(labelPos + (hasLabels ? 30 : 2), capRight);
      const svgH = end + ALONG / 2 + 4;
      geom = { vertical, len, top, end, trackX, tick1, tick2, labelPos, svgW, svgH };

      svg.setAttribute("width", svgW);
      svg.setAttribute("height", svgH);
      svg.setAttribute("viewBox", `0 0 ${svgW} ${svgH}`);

      slot.setAttribute("x1", trackX);
      slot.setAttribute("x2", trackX);
      slot.setAttribute("y1", top);
      slot.setAttribute("y2", end);

      const capC = end - f * len;
      fill.setAttribute("x1", trackX);
      fill.setAttribute("x2", trackX);
      fill.setAttribute("y1", capC);
      fill.setAttribute("y2", end);

      cap.setAttribute("x", trackX - ACROSS / 2);
      cap.setAttribute("y", capC - ALONG / 2);
      cap.setAttribute("width", ACROSS);
      cap.setAttribute("height", ALONG);
      groove.setAttribute("x1", trackX - ACROSS / 2 + 5);
      groove.setAttribute("x2", trackX + ACROSS / 2 - 5);
      groove.setAttribute("y1", capC);
      groove.setAttribute("y2", capC);
    } else {
      const trackY = ACROSS / 2 + 2;
      const start = ALONG / 2 + 4; // left == min
      const end = start + len; // right == max
      const tick1 = trackY + SLOT_W / 2 + 1;
      const tick2 = tick1 + TICK_LEN;
      const labelPos = tick2 + 3;
      const svgW = end + ALONG / 2 + 4;
      // Include the cap's bottom edge so it isn't clipped when there are no labels.
      const capBottom = trackY + ACROSS / 2 + 2;
      const svgH = Math.max(labelPos + (hasLabels ? 14 : 2), capBottom);
      geom = { vertical, len, start, end, trackY, tick1, tick2, labelPos, svgW, svgH };

      svg.setAttribute("width", svgW);
      svg.setAttribute("height", svgH);
      svg.setAttribute("viewBox", `0 0 ${svgW} ${svgH}`);

      slot.setAttribute("y1", trackY);
      slot.setAttribute("y2", trackY);
      slot.setAttribute("x1", start);
      slot.setAttribute("x2", end);

      const capC = start + f * len;
      fill.setAttribute("y1", trackY);
      fill.setAttribute("y2", trackY);
      fill.setAttribute("x1", start);
      fill.setAttribute("x2", capC);

      cap.setAttribute("x", capC - ALONG / 2);
      cap.setAttribute("y", trackY - ACROSS / 2);
      cap.setAttribute("width", ALONG);
      cap.setAttribute("height", ACROSS);
      groove.setAttribute("y1", trackY - ACROSS / 2 + 5);
      groove.setAttribute("y2", trackY + ACROSS / 2 - 5);
      groove.setAttribute("x1", capC);
      groove.setAttribute("x2", capC);
    }

    drawTicks(vertical, geom);
    updateValueLabel();
  }

  function updateTitle() {
    const text = model.get("label");
    title.textContent = text || "";
    title.style.display = text ? "" : "none";
  }

  function updateValueLabel() {
    if (!model.get("show_value")) {
      valueLabel.style.display = "none";
      return;
    }
    valueLabel.style.display = "";
    const value = model.get("value");
    const steps = model.get("steps") || [];
    if (steps.length) {
      const ticks = model.get("ticks") || [];
      const match = ticks.find((t) => Math.abs(t.value - value) < 1e-9);
      valueLabel.textContent = match ? match.label : String(value);
    } else {
      valueLabel.textContent = formatValue(value, model.get("step"));
    }
  }

  function pointerFraction(event) {
    const rect = svg.getBoundingClientRect();
    if (!geom) return valueFraction();
    let f;
    if (geom.vertical) {
      const scale = rect.height / geom.svgH;
      const y = (event.clientY - rect.top) / scale;
      f = (geom.end - y) / geom.len;
    } else {
      const scale = rect.width / geom.svgW;
      const x = (event.clientX - rect.left) / scale;
      f = (x - geom.start) / geom.len;
    }
    return Math.max(0, Math.min(1, f));
  }

  function setFromFraction(fraction) {
    const min = model.get("min_value");
    const max = model.get("max_value");
    const steps = model.get("steps") || [];
    const raw = min + fraction * (max - min);
    const next = steps.length
      ? nearestStep(raw, steps)
      : snap(raw, min, max, model.get("step"));
    model.set("value", next);
    model.save_changes();
  }

  function startDrag(event) {
    event.preventDefault();
    dragging = true;
    setFromFraction(pointerFraction(event));
  }
  function moveDrag(event) {
    if (!dragging) return;
    event.preventDefault();
    setFromFraction(pointerFraction(event));
  }
  function endDrag() {
    dragging = false;
  }

  svg.addEventListener("mousedown", startDrag);
  window.addEventListener("mousemove", moveDrag);
  window.addEventListener("mouseup", endDrag);
  svg.addEventListener(
    "touchstart",
    (e) => {
      if (e.touches.length) startDrag(e.touches[0]);
    },
    { passive: false },
  );
  window.addEventListener(
    "touchmove",
    (e) => {
      if (dragging && e.touches.length) moveDrag(e.touches[0]);
    },
    { passive: false },
  );
  window.addEventListener("touchend", endDrag);

  function applyColor() {
    const color = model.get("color");
    if (color) {
      wrapper.style.setProperty("--fader-fill", color);
      wrapper.style.setProperty("--fader-cap-border", color);
    } else {
      wrapper.style.removeProperty("--fader-fill");
      wrapper.style.removeProperty("--fader-cap-border");
    }
  }

  // --- MIDI (Ableton-style learn) -----------------------------------------
  let midiInputs = [];
  let midiStateBound = false;

  // Persist bindings in browser localStorage, namespaced by scope + key so two
  // notebooks (which share an origin's storage) don't collide. The default
  // scope is the browser URL path — localStorage is already per-origin, so the
  // path is all that's needed to tell sibling notebooks apart.
  function midiScope() {
    const explicit = model.get("midi_scope");
    if (explicit) return explicit;
    try {
      return window.location.pathname || "";
    } catch (e) {
      return "";
    }
  }

  function storageKey() {
    const key = model.get("midi_key") || model.get("label") || "";
    if (!key) return null;
    return `wigglystuff-midi/${midiScope()}/${key}`;
  }

  function saveBinding() {
    const sk = storageKey();
    if (!sk) return;
    try {
      localStorage.setItem(
        sk,
        JSON.stringify({
          cc: model.get("midi_cc"),
          channel: model.get("midi_channel"),
          device: model.get("midi_device"),
        }),
      );
    } catch (e) {
      /* storage unavailable (private mode, quota) — ignore */
    }
  }

  function clearBinding() {
    const sk = storageKey();
    if (!sk) return;
    try {
      localStorage.removeItem(sk);
    } catch (e) {
      /* ignore */
    }
  }

  function loadBinding() {
    const sk = storageKey();
    if (!sk) return null;
    try {
      const raw = localStorage.getItem(sk);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function onMidiMessage(event) {
    const [status, data1, data2] = event.data;
    if ((status & 0xf0) !== 0xb0) return; // control-change only
    const channel = status & 0x0f;
    const cc = data1;
    const val = data2;

    if (model.get("midi_learning")) {
      model.set("midi_cc", cc);
      model.set("midi_channel", channel);
      model.set("midi_device", event.target.name || "");
      model.set("midi_learning", false);
      model.save_changes();
      saveBinding();
      return;
    }

    const boundCc = model.get("midi_cc");
    if (boundCc < 0 || cc !== boundCc) return;
    const boundCh = model.get("midi_channel");
    if (boundCh >= 0 && channel !== boundCh) return;
    setFromFraction(val / 127);
  }

  function detachMidi() {
    for (const input of midiInputs) {
      input.removeEventListener("midimessage", onMidiMessage);
    }
    midiInputs = [];
  }

  function attachMidi(access) {
    detachMidi();
    for (const input of access.inputs.values()) {
      input.addEventListener("midimessage", onMidiMessage);
      midiInputs.push(input);
    }
  }

  async function enableMidi() {
    const access = await getMidiAccess();
    if (!access) return null;
    attachMidi(access);
    if (!midiStateBound) {
      midiStateBound = true;
      access.addEventListener("statechange", () => attachMidi(access));
    }
    return access;
  }

  function updateMidiButton() {
    if (!model.get("midi")) {
      midiBtn.style.display = "none";
      return;
    }
    midiBtn.style.display = "";
    midiBtn.classList.toggle("learning", model.get("midi_learning"));
    const cc = model.get("midi_cc");
    midiBtn.classList.toggle("bound", cc >= 0 && !model.get("midi_learning"));
    if (!model.get("midi_supported")) {
      midiBtn.textContent = "no MIDI";
      midiBtn.disabled = true;
      midiBtn.title = "Web MIDI is not available in this browser.";
    } else if (model.get("midi_learning")) {
      midiBtn.textContent = "move a control…";
      midiBtn.disabled = false;
      midiBtn.title = "Move a knob/fader on your MIDI device to bind it.";
    } else if (cc >= 0) {
      midiBtn.textContent = `CC ${cc}`;
      midiBtn.disabled = false;
      midiBtn.title =
        (model.get("midi_device") || "MIDI") +
        ` · CC ${cc}. Click to re-learn, right-click to clear.`;
    } else {
      midiBtn.textContent = "MIDI";
      midiBtn.disabled = false;
      midiBtn.title = "Click, then move a control on your MIDI device.";
    }
  }

  midiBtn.addEventListener("click", async () => {
    if (!model.get("midi_supported")) return;
    if (model.get("midi_learning")) {
      model.set("midi_learning", false); // toggle off
      model.save_changes();
      return;
    }
    await enableMidi();
    model.set("midi_learning", true);
    model.save_changes();
  });

  midiBtn.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    model.set("midi_cc", -1);
    model.set("midi_channel", -1);
    model.set("midi_device", "");
    model.set("midi_learning", false);
    model.save_changes();
    clearBinding();
  });

  function initMidi() {
    if (!model.get("midi")) {
      updateMidiButton();
      return;
    }
    const supported = !!navigator.requestMIDIAccess;
    if (model.get("midi_supported") !== supported) {
      model.set("midi_supported", supported);
      model.save_changes();
    }
    // Restore a persisted binding when none was set explicitly in Python.
    if (model.get("midi_cc") < 0) {
      const stored = loadBinding();
      if (stored && typeof stored.cc === "number" && stored.cc >= 0) {
        model.set("midi_cc", stored.cc);
        model.set(
          "midi_channel",
          typeof stored.channel === "number" ? stored.channel : -1,
        );
        model.set("midi_device", stored.device || "");
        model.save_changes();
      }
    }
    if (supported && model.get("midi_cc") >= 0) enableMidi();
    updateMidiButton();
  }

  model.on("change:value", updateGeometry);
  model.on("change:min_value", updateGeometry);
  model.on("change:max_value", updateGeometry);
  model.on("change:step", updateValueLabel);
  model.on("change:ticks", updateGeometry);
  model.on("change:steps", updateValueLabel);
  model.on("change:orientation", updateGeometry);
  model.on("change:length", updateGeometry);
  model.on("change:show_value", updateValueLabel);
  model.on("change:label", updateTitle);
  model.on("change:color", applyColor);
  model.on("change:midi", initMidi);
  model.on("change:midi_learning", updateMidiButton);
  model.on("change:midi_supported", updateMidiButton);
  model.on("change:midi_cc", updateMidiButton);
  model.on("change:midi_device", updateMidiButton);

  applyColor();
  updateTitle();
  updateGeometry();
  initMidi();

  return () => {
    window.removeEventListener("mousemove", moveDrag);
    window.removeEventListener("mouseup", endDrag);
    window.removeEventListener("touchmove", moveDrag);
    window.removeEventListener("touchend", endDrag);
    detachMidi();
  };
}

export default { render };
