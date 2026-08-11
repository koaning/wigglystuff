const SVG_NS = "http://www.w3.org/2000/svg";
const DEG = Math.PI / 180;

// Shared across all knobs on the page so we only request access once.
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

// A point on a circle, angle in degrees measured clockwise from 12 o'clock.
function pointAt(cx, cy, r, angleDeg) {
  const a = angleDeg * DEG;
  return { x: cx + r * Math.sin(a), y: cy - r * Math.cos(a) };
}

// SVG arc from angle a to angle b (degrees clockwise from top), drawn clockwise.
function arcPath(cx, cy, r, aDeg, bDeg) {
  const delta = bDeg - aDeg;
  if (Math.abs(delta) < 1e-6) return "";
  const sweep = delta > 0 ? 1 : 0;
  // A single SVG arc can't draw a full circle (endpoints coincide and the
  // renderer skips it), so split a full sweep into two semicircles.
  if (Math.abs(delta) >= 360 - 1e-6) {
    const p0 = pointAt(cx, cy, r, aDeg);
    const pm = pointAt(cx, cy, r, aDeg + 180);
    return `M ${p0.x} ${p0.y} A ${r} ${r} 0 1 ${sweep} ${pm.x} ${pm.y} A ${r} ${r} 0 1 ${sweep} ${p0.x} ${p0.y}`;
  }
  const a = pointAt(cx, cy, r, aDeg);
  const b = pointAt(cx, cy, r, bDeg);
  const large = Math.abs(delta) > 180 ? 1 : 0;
  return `M ${a.x} ${a.y} A ${r} ${r} 0 ${large} ${sweep} ${b.x} ${b.y}`;
}

function render({ model, el }) {
  el.innerHTML = "";

  const wrapper = document.createElement("div");
  wrapper.className = "knob-wrapper";

  const title = document.createElement("div");
  title.className = "knob-title";
  wrapper.appendChild(title);

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "knob-svg");

  const track = document.createElementNS(SVG_NS, "path");
  track.setAttribute("class", "knob-track");
  svg.appendChild(track);

  const fill = document.createElementNS(SVG_NS, "path");
  fill.setAttribute("class", "knob-fill");
  svg.appendChild(fill);

  const ticksGroup = document.createElementNS(SVG_NS, "g");
  ticksGroup.setAttribute("class", "knob-ticks");
  svg.appendChild(ticksGroup);

  const body = document.createElementNS(SVG_NS, "circle");
  body.setAttribute("class", "knob-body");
  svg.appendChild(body);

  const pointer = document.createElementNS(SVG_NS, "line");
  pointer.setAttribute("class", "knob-pointer");
  svg.appendChild(pointer);

  wrapper.appendChild(svg);

  const valueLabel = document.createElement("div");
  valueLabel.className = "knob-value";
  wrapper.appendChild(valueLabel);

  const midiBtn = document.createElement("button");
  midiBtn.className = "knob-midi-btn";
  midiBtn.type = "button";
  wrapper.appendChild(midiBtn);

  el.appendChild(wrapper);

  let dragging = false;

  function angleFor(fraction) {
    const start = model.get("start_angle");
    const end = model.get("end_angle");
    return start + fraction * (end - start);
  }

  function valueFraction() {
    const min = model.get("min_value");
    const max = model.get("max_value");
    return (model.get("value") - min) / (max - min);
  }

  function drawTicks(cx, cy, tickIn, tickOut, labelR) {
    ticksGroup.innerHTML = "";
    const ticks = model.get("ticks") || [];
    const min = model.get("min_value");
    const max = model.get("max_value");
    const span = max - min;
    if (span === 0) return;
    for (const t of ticks) {
      const f = (t.value - min) / span;
      if (f < -1e-6 || f > 1 + 1e-6) continue;
      const angle = angleFor(f);
      const p1 = pointAt(cx, cy, tickIn, angle);
      const p2 = pointAt(cx, cy, tickOut, angle);
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("class", "knob-tick");
      line.setAttribute("x1", p1.x);
      line.setAttribute("y1", p1.y);
      line.setAttribute("x2", p2.x);
      line.setAttribute("y2", p2.y);
      ticksGroup.appendChild(line);
      if (t.label) {
        const lp = pointAt(cx, cy, labelR, angle);
        const text = document.createElementNS(SVG_NS, "text");
        text.setAttribute("class", "knob-tick-label");
        text.setAttribute("x", lp.x);
        text.setAttribute("y", lp.y);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "middle");
        text.textContent = t.label;
        ticksGroup.appendChild(text);
      }
    }
  }

  function updateGeometry() {
    const size = model.get("size");
    svg.setAttribute("width", size);
    svg.setAttribute("height", size);
    svg.setAttribute("viewBox", `0 0 ${size} ${size}`);
    wrapper.style.width = size + "px";

    const cx = size / 2;
    const cy = size / 2;
    const R = size / 2;
    const ticks = model.get("ticks") || [];
    const hasLabels = ticks.some((t) => t.label);
    const pad = hasLabels ? 14 : 4;
    const outer = R - pad;

    const arcR = outer * 0.8;
    const bodyR = outer * 0.58;
    const tickIn = outer * 0.86;
    const tickOut = outer * 0.98;
    const labelR = outer + pad * 0.5;
    const arcWidth = Math.max(4, outer * 0.14);

    const start = model.get("start_angle");
    const end = model.get("end_angle");

    track.setAttribute("d", arcPath(cx, cy, arcR, start, end));
    track.setAttribute("stroke-width", arcWidth);

    const angle = angleFor(valueFraction());
    fill.setAttribute("d", arcPath(cx, cy, arcR, start, angle));
    fill.setAttribute("stroke-width", arcWidth);

    body.setAttribute("cx", cx);
    body.setAttribute("cy", cy);
    body.setAttribute("r", bodyR);

    const tip = pointAt(cx, cy, bodyR * 0.92, angle);
    const base = pointAt(cx, cy, bodyR * 0.15, angle);
    pointer.setAttribute("x1", base.x);
    pointer.setAttribute("y1", base.y);
    pointer.setAttribute("x2", tip.x);
    pointer.setAttribute("y2", tip.y);
    pointer.setAttribute("stroke-width", Math.max(2, bodyR * 0.12));

    drawTicks(cx, cy, tickIn, tickOut, labelR);
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
      // Prefer the matching tick label (so named detents read out by name).
      const ticks = model.get("ticks") || [];
      const match = ticks.find((t) => Math.abs(t.value - value) < 1e-9);
      valueLabel.textContent = match ? match.label : String(value);
    } else {
      valueLabel.textContent = formatValue(value, model.get("step"));
    }
  }

  // Map a pointer position to a fraction along the sweep, clamping into the
  // bottom gap rather than wrapping around like a full-circle dial.
  function pointerFraction(event) {
    const rect = svg.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = event.clientX - cx;
    const dy = event.clientY - cy;
    let a = Math.atan2(dx, -dy) / DEG; // degrees clockwise from top, (-180,180]
    const start = model.get("start_angle");
    const end = model.get("end_angle");
    while (a < start) a += 360;
    while (a >= start + 360) a -= 360;
    const sweep = end - start;
    if (a <= end) return (a - start) / sweep;
    // Pointer is in the gap beyond the arc: clamp to the nearer end.
    const gapMid = (end + start + 360) / 2;
    return a < gapMid ? 1 : 0;
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
      wrapper.style.setProperty("--knob-fill", color);
      wrapper.style.setProperty("--knob-pointer", color);
    } else {
      wrapper.style.removeProperty("--knob-fill");
      wrapper.style.removeProperty("--knob-pointer");
    }
  }

  // --- MIDI (Ableton-style learn) -----------------------------------------
  let midiInputs = [];
  let midiStateBound = false;

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
    // If a binding was restored from Python, start listening immediately.
    if (supported && model.get("midi_cc") >= 0) enableMidi();
    updateMidiButton();
  }

  model.on("change:value", updateGeometry);
  model.on("change:min_value", updateGeometry);
  model.on("change:max_value", updateGeometry);
  model.on("change:step", updateValueLabel);
  model.on("change:start_angle", updateGeometry);
  model.on("change:end_angle", updateGeometry);
  model.on("change:ticks", updateGeometry);
  model.on("change:steps", updateValueLabel);
  model.on("change:size", updateGeometry);
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
