const TAU = Math.PI * 2;
const HALF_PI = Math.PI / 2;

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

// Map a value in [start, stop] to a fraction in [0, 1].
function valueToFraction(value, start, stop) {
  return (value - start) / (stop - start);
}

// Map a fraction in [0, 1] to a canvas angle (radians).
// fraction 0 is at 12 o'clock; increases clockwise.
function fractionToAngle(fraction) {
  return -HALF_PI + fraction * TAU;
}

// Map a canvas angle (radians) to a fraction in [0, 1] using the
// "12 o'clock, clockwise" convention.
function angleToFraction(angle) {
  let f = (angle + HALF_PI) / TAU;
  f = ((f % 1) + 1) % 1;
  return f;
}

function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.className = "circular-slider-wrapper";

  const title = document.createElement("div");
  title.className = "circular-slider-title";
  wrapper.appendChild(title);

  const canvas = document.createElement("canvas");
  canvas.className = "circular-slider-canvas";
  wrapper.appendChild(canvas);

  const label = document.createElement("div");
  label.className = "circular-slider-label";
  wrapper.appendChild(label);

  el.appendChild(wrapper);

  const ctx = canvas.getContext("2d");
  let dragging = null; // null | "single" | "low" | "high" | "range-translate"
  let translateState = null; // { lastFraction: number } when dragging === "range-translate"

  function sizePx() {
    return model.get("size");
  }

  function thicknessPx() {
    return model.get("thickness");
  }

  function radiusPx() {
    return sizePx() / 2 - thicknessPx() / 2 - 2;
  }

  function resizeCanvas() {
    const px = sizePx();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = px * dpr;
    canvas.height = px * dpr;
    canvas.style.width = px + "px";
    canvas.style.height = px + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    wrapper.style.width = px + "px";
  }

  function readColor(name) {
    return getComputedStyle(wrapper).getPropertyValue(name).trim();
  }

  function drawTrack() {
    const cx = sizePx() / 2;
    const cy = sizePx() / 2;
    const r = radiusPx();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, TAU);
    ctx.strokeStyle = readColor("--cs-track");
    ctx.lineWidth = thicknessPx();
    ctx.lineCap = "butt";
    ctx.stroke();
  }

  function drawFillArc(fracA, fracB) {
    if (fracA === fracB) return;
    const cx = sizePx() / 2;
    const cy = sizePx() / 2;
    const r = radiusPx();
    const a = fractionToAngle(fracA);
    let b = fractionToAngle(fracB);
    // Ensure we always sweep clockwise from a to b, wrapping through the
    // 12 o'clock seam if fracB < fracA.
    if (b <= a) b += TAU;
    ctx.beginPath();
    ctx.arc(cx, cy, r, a, b);
    ctx.strokeStyle = readColor("--cs-fill");
    ctx.lineWidth = thicknessPx();
    ctx.lineCap = "round";
    ctx.stroke();
  }

  function drawHandle(fraction) {
    const cx = sizePx() / 2;
    const cy = sizePx() / 2;
    const r = radiusPx();
    const angle = fractionToAngle(fraction);
    const hx = cx + r * Math.cos(angle);
    const hy = cy + r * Math.sin(angle);
    const handleRadius = Math.max(8, thicknessPx() * 0.55);
    ctx.beginPath();
    ctx.arc(hx, hy, handleRadius, 0, TAU);
    ctx.fillStyle = readColor("--cs-handle");
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = readColor("--cs-handle-border");
    ctx.stroke();
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

  function getMode() {
    return model.get("_mode");
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawTrack();

    const start = model.get("start");
    const stop = model.get("stop");
    const mode = getMode();

    if (mode === "range") {
      const v = model.get("value");
      const fa = valueToFraction(v[0], start, stop);
      const fb = valueToFraction(v[1], start, stop);
      drawFillArc(fa, fb);
      drawHandle(fa);
      drawHandle(fb);
    } else {
      const v = model.get("value");
      const fb = valueToFraction(v, start, stop);
      if (fb > 0.0001) drawFillArc(0, fb);
      drawHandle(fb);
    }
    updateLabel();
  }

  function pointFraction(event) {
    const rect = canvas.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = event.clientX - cx;
    const dy = event.clientY - cy;
    const angle = Math.atan2(dy, dx);
    return angleToFraction(angle);
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
    // No swap — let the range cross the 12 o'clock seam so dragging
    // either handle past the other wraps naturally.
    model.set("value", [lo, hi]);
    model.save_changes();
  }

  // Smallest distance between two fractions on the unit circle.
  function circularDist(a, b) {
    const d = Math.abs(a - b);
    return Math.min(d, 1 - d);
  }

  // Handle radius in fraction units — clicks within this of a handle pick that
  // handle even if they technically land in the fill arc.
  function handleFractionRadius() {
    const r = radiusPx();
    if (r <= 0) return 0;
    const handlePx = Math.max(8, thicknessPx() * 0.55);
    return handlePx / (TAU * r);
  }

  // Is `fraction` inside the fill arc that sweeps clockwise from fLow to fHigh?
  // Handles the wrap-around case where fLow > fHigh.
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

      // If close enough to a handle, drag that handle.
      if (distLow <= handleR || distHigh <= handleR) {
        dragging = distLow <= distHigh ? "low" : "high";
        setRangeFromFraction(dragging, fraction);
        return;
      }
      // Otherwise, if the click is inside the fill arc, translate the whole span.
      if (isInsideFillArc(fraction, fLow, fHigh)) {
        dragging = "range-translate";
        translateState = { lastFraction: fraction };
        return;
      }
      // Click landed on bare track outside the fill — move the closer handle there.
      dragging = distLow <= distHigh ? "low" : "high";
      setRangeFromFraction(dragging, fraction);
    } else {
      dragging = "single";
      setSingleFromFraction(fraction);
    }
  }

  function translateRange(fraction) {
    // Wrap-aware delta in fraction units.
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

  canvas.addEventListener("mousedown", startDrag);
  window.addEventListener("mousemove", moveDrag);
  window.addEventListener("mouseup", endDrag);

  canvas.addEventListener("touchstart", (e) => {
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

  model.on("change:value", draw);
  model.on("change:start", draw);
  model.on("change:stop", draw);
  model.on("change:step", draw);
  model.on("change:show_value", draw);
  model.on("change:thickness", draw);
  model.on("change:color", () => {
    applyColor();
    draw();
  });
  model.on("change:label", updateTitle);
  model.on("change:size", () => {
    resizeCanvas();
    draw();
  });

  applyColor();
  updateTitle();
  resizeCanvas();
  draw();

  return () => {
    window.removeEventListener("mousemove", moveDrag);
    window.removeEventListener("mouseup", endDrag);
    window.removeEventListener("touchmove", moveDrag);
    window.removeEventListener("touchend", endDrag);
  };
}

export default { render };
