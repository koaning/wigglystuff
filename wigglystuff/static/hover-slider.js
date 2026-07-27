function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "hover-slider";
  root.tabIndex = 0;
  root.setAttribute("role", "slider");

  const labelEl = document.createElement("div");
  labelEl.className = "hover-slider-label";

  // The track is the only hit target; everything inside it is pointer-events: none.
  const track = document.createElement("div");
  track.className = "hover-slider-track";

  const rail = document.createElement("div");
  rail.className = "hover-slider-rail";
  const fill = document.createElement("div");
  fill.className = "hover-slider-fill";
  const ghost = document.createElement("div");
  ghost.className = "hover-slider-ghost";
  const puck = document.createElement("div");
  puck.className = "hover-slider-puck";
  track.append(rail, fill, ghost, puck);

  const readout = document.createElement("div");
  readout.className = "hover-slider-readout";
  const readoutValue = document.createElement("span");
  readoutValue.className = "hover-slider-readout-value";
  const readoutHover = document.createElement("span");
  readoutHover.className = "hover-slider-readout-hover";
  readout.append(readoutValue, readoutHover);

  root.append(labelEl, track, readout);
  el.appendChild(root);

  let dragging = false;
  let hovering = false;

  // --- syncing ---------------------------------------------------------------
  // model.set() is local and anywidget accumulates the dirty diff, so we set on
  // every pointer move (DOM stays smooth) and throttle only save_changes().
  let syncTimer = null;
  let syncPending = false;

  function queueSync() {
    const ms = model.get("sync_throttle_ms") ?? 100;
    if (ms <= 0) {
      forceSync();
      return;
    }
    // Remember that newer state exists even if a flush is already scheduled --
    // that trailing flush is what stops the final hover position being dropped.
    syncPending = true;
    if (syncTimer !== null) return;
    syncTimer = setTimeout(() => {
      syncTimer = null;
      if (syncPending) {
        syncPending = false;
        model.save_changes();
      }
    }, ms);
  }

  function forceSync() {
    if (syncTimer !== null) {
      clearTimeout(syncTimer);
      syncTimer = null;
    }
    syncPending = false;
    model.save_changes();
  }

  // --- value <-> pixel ------------------------------------------------------
  function decimals(step) {
    const text = String(step);
    const dot = text.indexOf(".");
    return dot === -1 ? 0 : text.length - dot - 1;
  }

  function pointerFraction(event) {
    const rect = track.getBoundingClientRect();
    if (rect.width <= 0) return 0;
    return Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  }

  function valueToIndex(value) {
    const steps = model.get("steps");
    let best = 0;
    for (let i = 1; i < steps.length; i++) {
      if (Math.abs(steps[i] - value) < Math.abs(steps[best] - value)) best = i;
    }
    return best;
  }

  function fractionToValue(fraction) {
    const steps = model.get("steps");
    if (steps.length) {
      // Discrete mode is laid out in index space, so steps=[1, 10, 100, 1000]
      // renders as four evenly spaced positions.
      const last = steps.length - 1;
      return steps[Math.max(0, Math.min(last, Math.round(fraction * last)))];
    }
    const start = model.get("start");
    const stop = model.get("stop");
    const step = model.get("step") || 1;
    const raw = start + fraction * (stop - start);
    const snapped = start + Math.round((raw - start) / step) * step;
    return Number(
      Math.max(start, Math.min(stop, snapped)).toFixed(decimals(step)),
    );
  }

  function valueToFraction(value) {
    const steps = model.get("steps");
    if (steps.length) {
      return valueToIndex(value) / (steps.length - 1);
    }
    const start = model.get("start");
    const stop = model.get("stop");
    return stop === start ? 0 : (value - start) / (stop - start);
  }

  function format(value) {
    const steps = model.get("steps");
    return steps.length
      ? String(value)
      : value.toFixed(decimals(model.get("step") || 1));
  }

  // --- painting -------------------------------------------------------------
  function applyColor() {
    const color = model.get("color");
    for (const name of ["--hs-fill", "--hs-puck-border", "--hs-ghost"]) {
      if (color) root.style.setProperty(name, color);
      else root.style.removeProperty(name);
    }
  }

  function paint() {
    root.style.width = model.get("width") + "px";

    const value = model.get("value");
    const live = model.get("hovering");
    const fraction = valueToFraction(value);

    fill.style.width = fraction * 100 + "%";
    puck.style.left = fraction * 100 + "%";
    ghost.style.display = live ? "" : "none";
    if (live) {
      ghost.style.left = valueToFraction(model.get("hover_value")) * 100 + "%";
    }

    const label = model.get("label");
    labelEl.textContent = label;
    labelEl.style.display = label ? "" : "none";

    readout.style.display = model.get("show_value") ? "" : "none";
    readoutValue.textContent = format(value);
    readoutHover.textContent = live ? "→ " + format(model.get("hover_value")) : "";

    const steps = model.get("steps");
    root.setAttribute("aria-valuemin", String(steps.length ? steps[0] : model.get("start")));
    root.setAttribute(
      "aria-valuemax",
      String(steps.length ? steps[steps.length - 1] : model.get("stop")),
    );
    root.setAttribute("aria-valuenow", String(value));
    root.classList.toggle("is-hovering", live);
  }

  // --- pointer --------------------------------------------------------------
  // Pointer events cover mouse, pen and touch in one path, and pointer capture
  // on the track means no window-level listeners to clean up.
  track.addEventListener("pointerenter", (event) => {
    hovering = true;
    model.set("hovering", true);
    model.set("hover_value", fractionToValue(pointerFraction(event)));
    paint();
    forceSync();
  });

  track.addEventListener("pointermove", (event) => {
    if (!dragging && !hovering) return;
    const next = fractionToValue(pointerFraction(event));
    if (dragging) {
      if (next === model.get("value")) return;
      model.set("value", next);
      model.set("hover_value", next);
    } else {
      if (next === model.get("hover_value")) return;
      model.set("hover_value", next);
    }
    paint();
    queueSync();
  });

  track.addEventListener("pointerleave", () => {
    if (dragging) return; // pointer capture keeps the drag alive off-track
    hovering = false;
    model.set("hovering", false);
    model.set("hover_value", model.get("value"));
    paint();
    forceSync();
  });

  // Commit on pointerdown rather than click; doing both would double-commit.
  track.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    dragging = true;
    hovering = true;
    track.setPointerCapture(event.pointerId);
    root.focus({ preventScroll: true });
    const next = fractionToValue(pointerFraction(event));
    model.set("value", next);
    model.set("hover_value", next);
    model.set("hovering", true);
    paint();
    forceSync();
  });

  function endDrag(event) {
    if (!dragging) return;
    dragging = false;
    try {
      track.releasePointerCapture(event.pointerId);
    } catch {
      // pointer already gone; nothing to release
    }
    paint(); // let anything Python changed mid-drag land now
    forceSync();
  }
  track.addEventListener("pointerup", endDrag);
  track.addEventListener("pointercancel", endDrag);

  // --- keyboard -------------------------------------------------------------
  function neighbour(delta) {
    const steps = model.get("steps");
    if (steps.length) {
      const index = Math.max(
        0,
        Math.min(steps.length - 1, valueToIndex(model.get("value")) + delta),
      );
      return steps[index];
    }
    const step = model.get("step") || 1;
    return fractionToValue(valueToFraction(model.get("value") + delta * step));
  }

  root.addEventListener("keydown", (event) => {
    const steps = model.get("steps");
    let next;
    if (event.key === "ArrowRight" || event.key === "ArrowUp") next = neighbour(1);
    else if (event.key === "ArrowLeft" || event.key === "ArrowDown") next = neighbour(-1);
    else if (event.key === "Home") next = steps.length ? steps[0] : model.get("start");
    else if (event.key === "End")
      next = steps.length ? steps[steps.length - 1] : model.get("stop");
    else return;

    event.preventDefault();
    event.stopPropagation(); // marimo and Jupyter bind global arrow keys

    if (next === model.get("value")) return;
    model.set("value", next);
    if (!hovering) model.set("hover_value", next);
    paint();
    forceSync(); // a keypress is a discrete commit, no reason to delay it
  });

  // --- model -> view --------------------------------------------------------
  // Never call save_changes() from these handlers, and never repaint mid-drag.
  const watched = [
    "value",
    "hover_value",
    "hovering",
    "start",
    "stop",
    "step",
    "steps",
    "show_value",
    "label",
    "width",
  ];
  for (const name of watched) {
    model.on(`change:${name}`, () => {
      if (!dragging) paint();
    });
  }
  model.on("change:color", applyColor);

  applyColor();
  paint();

  return () => {
    if (syncTimer !== null) clearTimeout(syncTimer);
  };
}

export default { render };
