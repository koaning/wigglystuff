const TAU = Math.PI * 2;
const HALF_PI = Math.PI / 2;
const SVG_NS = "http://www.w3.org/2000/svg";

function getPrecision(step) {
  const s = String(step);
  const dot = s.indexOf(".");
  return dot === -1 ? 0 : s.length - dot - 1;
}

function snap(value, start, stop, step) {
  const clamped = Math.max(start, Math.min(stop, value));
  const snapped = start + Math.round((clamped - start) / step) * step;
  return Math.max(start, Math.min(stop, snapped));
}

function formatValue(value, step) {
  return value.toFixed(getPrecision(step));
}

function valueToFraction(value, start, stop) {
  return (value - start) / (stop - start);
}

// fraction 0 is at 12 o'clock; increases clockwise.
function fractionToAngle(fraction) {
  return -HALF_PI + fraction * TAU;
}

function angleToFraction(angle) {
  let f = (angle + HALF_PI) / TAU;
  f = ((f % 1) + 1) % 1;
  return f;
}

function arcPath(cx, cy, r, fracA, fracB) {
  if (fracA === fracB) return "";
  const a = fractionToAngle(fracA);
  let b = fractionToAngle(fracB);
  if (b <= a) b += TAU;
  const sweep = b - a;
  const x1 = cx + r * Math.cos(a);
  const y1 = cy + r * Math.sin(a);
  // A single SVG arc command can't draw a full circle (endpoints coincide
  // and the renderer skips it). Split into two semicircles.
  if (sweep >= TAU - 1e-6) {
    const xm = cx + r * Math.cos(a + Math.PI);
    const ym = cy + r * Math.sin(a + Math.PI);
    return `M ${x1} ${y1} A ${r} ${r} 0 1 1 ${xm} ${ym} A ${r} ${r} 0 1 1 ${x1} ${y1}`;
  }
  const x2 = cx + r * Math.cos(b);
  const y2 = cy + r * Math.sin(b);
  const largeArc = sweep > Math.PI ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
}

function render({ model, el }) {
  el.innerHTML = "";

  const wrapper = document.createElement("div");
  wrapper.className = "circular-slider-wrapper";

  const title = document.createElement("div");
  title.className = "circular-slider-title";
  wrapper.appendChild(title);

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "circular-slider-svg");

  const track = document.createElementNS(SVG_NS, "circle");
  track.setAttribute("class", "circular-slider-track");
  svg.appendChild(track);

  const fill = document.createElementNS(SVG_NS, "path");
  fill.setAttribute("class", "circular-slider-fill");
  svg.appendChild(fill);

  const handleA = document.createElementNS(SVG_NS, "circle");
  handleA.setAttribute("class", "circular-slider-handle");
  svg.appendChild(handleA);

  const handleB = document.createElementNS(SVG_NS, "circle");
  handleB.setAttribute("class", "circular-slider-handle");
  svg.appendChild(handleB);

  wrapper.appendChild(svg);

  const label = document.createElement("div");
  label.className = "circular-slider-label";
  wrapper.appendChild(label);

  el.appendChild(wrapper);

  let dragging = null; // null | "single" | "low" | "high" | "range-translate"
  let translateState = null;

  function sizePx() {
    return model.get("size");
  }

  function thicknessPx() {
    return model.get("thickness");
  }

  function radiusPx() {
    return sizePx() / 2 - thicknessPx() / 2 - 2;
  }

  function handleRadiusPx() {
    return Math.max(8, thicknessPx() * 0.55);
  }

  function getMode() {
    return model.get("_mode");
  }

  function setHandle(node, fraction, visible) {
    if (!visible) {
      node.setAttribute("display", "none");
      return;
    }
    node.removeAttribute("display");
    const cx = sizePx() / 2;
    const cy = sizePx() / 2;
    const r = radiusPx();
    const angle = fractionToAngle(fraction);
    node.setAttribute("cx", cx + r * Math.cos(angle));
    node.setAttribute("cy", cy + r * Math.sin(angle));
    node.setAttribute("r", handleRadiusPx());
  }

  function updateGeometry() {
    const px = sizePx();
    svg.setAttribute("width", px);
    svg.setAttribute("height", px);
    svg.setAttribute("viewBox", `0 0 ${px} ${px}`);
    wrapper.style.width = px + "px";

    const cx = px / 2;
    const cy = px / 2;
    const r = radiusPx();
    const t = thicknessPx();

    track.setAttribute("cx", cx);
    track.setAttribute("cy", cy);
    track.setAttribute("r", r);
    track.setAttribute("stroke-width", t);

    fill.setAttribute("stroke-width", t);

    const start = model.get("start");
    const stop = model.get("stop");
    const mode = getMode();

    if (mode === "range") {
      const v = model.get("value");
      const fa = valueToFraction(v[0], start, stop);
      const fb = valueToFraction(v[1], start, stop);
      fill.setAttribute("d", arcPath(cx, cy, r, fa, fb));
      setHandle(handleA, fa, true);
      setHandle(handleB, fb, true);
    } else {
      const v = model.get("value");
      const fb = valueToFraction(v, start, stop);
      fill.setAttribute("d", fb > 0.0001 ? arcPath(cx, cy, r, 0, fb) : "");
      setHandle(handleA, fb, true);
      setHandle(handleB, 0, false);
    }
    updateLabel();
  }

  function updateTitle() {
    const text = model.get("label");
    if (text) {
      title.textContent = text;
      title.style.display = "";
    } else {
      title.textContent = "";
      title.style.display = "none";
    }
  }

  function updateLabel() {
    if (!model.get("show_value")) {
      label.style.display = "none";
      label.textContent = "";
      return;
    }
    label.style.display = "";
    const step = model.get("step");
    if (getMode() === "range") {
      const v = model.get("value");
      label.textContent = `${formatValue(v[0], step)} – ${formatValue(v[1], step)}`;
    } else {
      label.textContent = formatValue(model.get("value"), step);
    }
  }

  function pointFraction(event) {
    const rect = svg.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = event.clientX - cx;
    const dy = event.clientY - cy;
    return angleToFraction(Math.atan2(dy, dx));
  }

  function fractionToValue(fraction) {
    const start = model.get("start");
    const stop = model.get("stop");
    return start + fraction * (stop - start);
  }

  function setSingleFromFraction(fraction) {
    const start = model.get("start");
    const stop = model.get("stop");
    const step = model.get("step");
    const raw = fractionToValue(fraction);
    model.set("value", snap(raw, start, stop, step));
    model.save_changes();
  }

  function setRangeFromFraction(which, fraction) {
    const start = model.get("start");
    const stop = model.get("stop");
    const step = model.get("step");
    const raw = fractionToValue(fraction);
    const snapped = snap(raw, start, stop, step);
    const current = model.get("value");
    let lo = current[0];
    let hi = current[1];
    if (which === "low") lo = snapped;
    else hi = snapped;
    model.set("value", [lo, hi]);
    model.save_changes();
  }

  function circularDist(a, b) {
    const d = Math.abs(a - b);
    return Math.min(d, 1 - d);
  }

  // Handle radius in fraction units.
  function handleFractionRadius() {
    const r = radiusPx();
    if (r <= 0) return 0;
    return handleRadiusPx() / (TAU * r);
  }

  function isInsideFillArc(fraction, fLow, fHigh) {
    if (fLow === fHigh) return false;
    if (fLow < fHigh) {
      return fraction > fLow && fraction < fHigh;
    }
    return fraction > fLow || fraction < fHigh;
  }

  function startDrag(event) {
    event.preventDefault();
    const fraction = pointFraction(event);
    const mode = getMode();
    if (mode === "range") {
      const start = model.get("start");
      const stop = model.get("stop");
      const v = model.get("value");
      const fLow = valueToFraction(v[0], start, stop);
      const fHigh = valueToFraction(v[1], start, stop);
      const distLow = circularDist(fraction, fLow);
      const distHigh = circularDist(fraction, fHigh);
      const handleR = handleFractionRadius();

      if (distLow <= handleR || distHigh <= handleR) {
        dragging = distLow <= distHigh ? "low" : "high";
        setRangeFromFraction(dragging, fraction);
        return;
      }
      if (isInsideFillArc(fraction, fLow, fHigh)) {
        dragging = "range-translate";
        translateState = { lastFraction: fraction };
        return;
      }
      dragging = distLow <= distHigh ? "low" : "high";
      setRangeFromFraction(dragging, fraction);
    } else {
      dragging = "single";
      setSingleFromFraction(fraction);
    }
  }

  function translateRange(fraction) {
    let delta = fraction - translateState.lastFraction;
    if (delta > 0.5) delta -= 1;
    if (delta < -0.5) delta += 1;
    translateState.lastFraction = fraction;

    const start = model.get("start");
    const stop = model.get("stop");
    const step = model.get("step");
    const range = stop - start;
    if (range <= 0) return;
    const deltaValue = delta * range;

    function wrap(v) {
      return start + (((v - start) % range) + range) % range;
    }
    function snapToGrid(v) {
      return start + Math.round((v - start) / step) * step;
    }

    const current = model.get("value");
    const newLow = wrap(snapToGrid(current[0] + deltaValue));
    const newHigh = wrap(snapToGrid(current[1] + deltaValue));

    if (newLow !== current[0] || newHigh !== current[1]) {
      model.set("value", [newLow, newHigh]);
      model.save_changes();
    }
  }

  function moveDrag(event) {
    if (dragging === null) return;
    event.preventDefault();
    const fraction = pointFraction(event);
    if (dragging === "single") {
      setSingleFromFraction(fraction);
    } else if (dragging === "range-translate") {
      translateRange(fraction);
    } else {
      setRangeFromFraction(dragging, fraction);
    }
  }

  function endDrag() {
    dragging = null;
    translateState = null;
  }

  svg.addEventListener("mousedown", startDrag);
  window.addEventListener("mousemove", moveDrag);
  window.addEventListener("mouseup", endDrag);

  svg.addEventListener("touchstart", (e) => {
    if (e.touches.length === 0) return;
    startDrag(e.touches[0]);
  }, { passive: false });
  window.addEventListener("touchmove", (e) => {
    if (dragging === null) return;
    if (e.touches.length === 0) return;
    moveDrag(e.touches[0]);
  }, { passive: false });
  window.addEventListener("touchend", endDrag);

  function applyColor() {
    const color = model.get("color");
    if (color) {
      wrapper.style.setProperty("--cs-fill", color);
      wrapper.style.setProperty("--cs-handle-border", color);
    } else {
      wrapper.style.removeProperty("--cs-fill");
      wrapper.style.removeProperty("--cs-handle-border");
    }
  }

  model.on("change:value", updateGeometry);
  model.on("change:start", updateGeometry);
  model.on("change:stop", updateGeometry);
  model.on("change:step", updateGeometry);
  model.on("change:show_value", updateGeometry);
  model.on("change:thickness", updateGeometry);
  model.on("change:size", updateGeometry);
  model.on("change:color", applyColor);
  model.on("change:label", updateTitle);

  applyColor();
  updateTitle();
  updateGeometry();

  return () => {
    window.removeEventListener("mousemove", moveDrag);
    window.removeEventListener("mouseup", endDrag);
    window.removeEventListener("touchmove", moveDrag);
    window.removeEventListener("touchend", endDrag);
  };
}

export default { render };
