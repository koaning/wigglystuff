const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';
const PREV_ICON = '<svg viewBox="0 0 16 16"><rect x="2" y="2" width="2" height="12"/><polygon points="14,2 5,8 14,14"/></svg>';
const NEXT_ICON = '<svg viewBox="0 0 16 16"><polygon points="2,2 11,8 2,14"/><rect x="12" y="2" width="2" height="12"/></svg>';
const SVG_NS = "http://www.w3.org/2000/svg";

// Speed slider: 0..100 maps log-scale onto 1000ms .. 2ms per step.
const SLOWEST_MS = 1000;
const FASTEST_MS = 2;

function el(tag, className, textValue) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (textValue != null) node.textContent = textValue;
  return node;
}

function svgEl(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
  return node;
}

function button(icon, title) {
  const btn = el("button", "sv-btn");
  btn.type = "button";
  btn.title = title;
  btn.innerHTML = icon;
  return btn;
}

function codeLine(line, number) {
  const row = el("div", "sv-line");
  row.append(el("span", "sv-lineno", String(number)));
  const textNode = el("span", "sv-text");
  const tokens = [...(line.tokens || [])].sort((a, b) => a.start - b.start);
  let cursor = 0;
  for (const token of tokens) {
    if (token.start < cursor) continue;
    textNode.append(document.createTextNode(line.text.slice(cursor, token.start)));
    textNode.append(el("span", `sv-${token.type}`, line.text.slice(token.start, token.end)));
    cursor = token.end;
  }
  textNode.append(document.createTextNode(line.text.slice(cursor) || " "));
  row.append(textNode);
  return row;
}

function intervalToSlider(ms) {
  const t = Math.log(SLOWEST_MS / ms) / Math.log(SLOWEST_MS / FASTEST_MS);
  return Math.round(Math.max(0, Math.min(1, t)) * 100);
}

function sliderToInterval(value) {
  return SLOWEST_MS * Math.pow(FASTEST_MS / SLOWEST_MS, value / 100);
}

function render({ model, el: host }) {
  const uid = Math.random().toString(36).slice(2, 10);
  const root = el("div", "state-viewer-root");
  root.tabIndex = 0;

  const main = el("div", "sv-main");
  const viewPanel = el("div", "sv-view-panel");
  const view = el("div", "sv-view");
  viewPanel.append(view);

  const side = el("div", "sv-side");
  const codePanel = el("div", "sv-code");
  const localsPanel = el("div", "sv-locals");
  side.append(codePanel, localsPanel);
  main.append(viewPanel, side);

  const controls = el("div", "sv-controls");
  const prevBtn = button(PREV_ICON, "Previous step (←)");
  const playBtn = button(PLAY_ICON, "Play / pause (space)");
  const nextBtn = button(NEXT_ICON, "Next step (→)");
  const counter = el("span", "sv-counter");
  const depthBadge = el("span", "sv-depth");
  const speedWrap = el("label", "sv-speed");
  const speed = el("input", "sv-speed-range");
  speed.type = "range";
  speed.min = "0";
  speed.max = "100";
  const speedLabel = el("span", "sv-speed-label");
  speedWrap.append(speed, speedLabel);
  const status = el("span", "sv-status");
  controls.append(prevBtn, playBtn, nextBtn, counter, depthBadge, speedWrap, status);

  const timelineCaption = el("div", "sv-timeline-caption");
  const timelineLabel = el("span");
  timelineCaption.append(timelineLabel, el("span", "", "click or drag to scrub"));
  const timeline = svgEl("svg", { class: "sv-timeline", preserveAspectRatio: "none" });
  const errorBox = el("div", "sv-error");

  root.append(main, controls, timelineCaption, timeline, errorBox);
  host.append(root);

  let cur = 0;
  let rafId = null;
  let lastTime = 0;
  let pending = 0;
  let lineNodes = [];
  let playhead = null;
  let clipRect = null;
  let minViewWidth = 0;
  let minViewHeight = 0;

  const steps = () => model.get("steps") || [];
  // The number the timeline plots for a step: timeline_func's value if given.
  const metric = (s) => (s.value ?? s.depth);
  function badgeText(step) {
    const label = model.get("timeline_label");
    if (label === "call depth") return `depth ${step.depth}`;
    const v = metric(step);
    return `${label} ${Number.isInteger(v) ? v : v.toFixed(2)}`;
  }
  const maxIndex = () => Math.max(0, steps().length - 1);
  const clamp = (i) => Math.max(0, Math.min(i, maxIndex()));

  function buildCode() {
    codePanel.replaceChildren();
    lineNodes = (model.get("lines") || []).map((line, i) => {
      const row = codeLine(line, i + 1);
      codePanel.append(row);
      return row;
    });
  }

  function buildTimeline() {
    timeline.replaceChildren();
    const label = model.get("timeline_label");
    timelineLabel.textContent =
      label === "call depth"
        ? "call depth over the whole run (taller = deeper recursion)"
        : `${label} over the whole run`;
    const all = steps();
    if (!all.length) return;
    // Step-plot of each step's value (timeline_func, or the call depth),
    // rising from a baseline at 0 (or the minimum, if values go negative).
    const values = all.map(metric);
    const low = Math.min(0, ...values);
    const top = Math.max(low + 1, ...values);
    const span = top - low;
    timeline.setAttribute("viewBox", `0 0 ${all.length} ${span}`);
    let d = `M0,${span}`;
    values.forEach((v, i) => {
      d += ` V${top - v} H${i + 1}`;
    });
    d += ` V${span} Z`;
    const clipId = `sv-clip-${uid}`;
    const defs = svgEl("defs");
    const clip = svgEl("clipPath", { id: clipId });
    clipRect = svgEl("rect", { x: 0, y: 0, width: 0, height: span });
    clip.append(clipRect);
    defs.append(clip);
    timeline.append(
      defs,
      svgEl("path", { d, class: "sv-area-future" }),
      svgEl("path", { d, class: "sv-area-past", "clip-path": `url(#${clipId})` }),
    );
    playhead = svgEl("line", {
      class: "sv-playhead",
      x1: 0, x2: 0, y1: 0, y2: span,
      "vector-effect": "non-scaling-stroke",
    });
    timeline.append(playhead);
  }

  // One fixed row per variable the run ever assigns; names that aren't
  // assigned in the current frame yet show a muted placeholder.
  function renderLocals(step, previous) {
    localsPanel.replaceChildren();
    for (const name of model.get("variables") || []) {
      const value = step?.locals?.[name];
      const row = el("div", "sv-local");
      if (value === undefined) row.classList.add("sv-unset");
      else if (previous && previous.locals?.[name] !== value) row.classList.add("sv-changed");
      row.append(el("span", "sv-local-name", name));
      const valueNode = el("span", "sv-local-value", value === undefined ? "not assigned" : value);
      if (value !== undefined) valueNode.title = value;
      row.append(valueNode);
      localsPanel.append(row);
    }
  }

  function renderView(step) {
    const views = model.get("views") || [];
    // No view_func: the code and variables are the whole widget.
    viewPanel.style.display = views.length ? "" : "none";
    const html = step && step.view >= 0 ? views[step.view] : "";
    if (view.dataset.index !== String(step?.view)) {
      view.innerHTML = html || "";
      view.dataset.index = String(step?.view);
      // Grow-only minimum size so the layout doesn't jump when a view shrinks.
      minViewWidth = Math.max(minViewWidth, view.scrollWidth);
      minViewHeight = Math.max(minViewHeight, view.scrollHeight);
      view.style.minWidth = `${minViewWidth}px`;
      view.style.minHeight = `${minViewHeight}px`;
    }
  }

  function scrollCodeTo(node) {
    if (codePanel.scrollHeight <= codePanel.clientHeight) return;
    const top = node.offsetTop - codePanel.offsetTop;
    if (top < codePanel.scrollTop || top + node.offsetHeight > codePanel.scrollTop + codePanel.clientHeight) {
      codePanel.scrollTop = top - codePanel.clientHeight / 2;
    }
  }

  function renderStep() {
    const all = steps();
    cur = clamp(cur);
    const step = all[cur];
    const previous = cur > 0 ? all[cur - 1] : null;

    for (const node of lineNodes) {
      node.classList.remove("sv-current", "sv-return", "sv-raise");
      node.querySelector(".sv-pill")?.remove();
    }
    const lineNode = step ? lineNodes[step.line - 1] : null;
    if (lineNode) {
      lineNode.classList.add("sv-current");
      if (step.event === "return") {
        lineNode.classList.add("sv-return");
        lineNode.append(el("span", "sv-pill", `↩ ${step.returned}`));
      } else if (step.event === "raise") {
        lineNode.classList.add("sv-raise");
        lineNode.append(el("span", "sv-pill", "raise"));
      }
      scrollCodeTo(lineNode);
    }

    renderView(step);
    renderLocals(step, previous);

    counter.textContent = all.length ? `${cur + 1} / ${all.length}` : "0 / 0";
    depthBadge.textContent = step ? badgeText(step) : "";
    if (clipRect) clipRect.setAttribute("width", String(cur + 1));
    if (playhead) {
      playhead.setAttribute("x1", String(cur + 0.5));
      playhead.setAttribute("x2", String(cur + 0.5));
    }

    const parts = [];
    if (cur === maxIndex()) {
      if (model.get("error")) parts.push("raised");
      else if (model.get("truncated")) parts.push("stopped at max_steps");
      else if (model.get("returned") != null) parts.push(`returned ${model.get("returned")}`);
    }
    status.textContent = parts.join(" · ");
  }

  function renderError() {
    const error = model.get("error");
    errorBox.style.display = error ? "" : "none";
    if (!error) return;
    const where = error.lineno ? ` (line ${error.lineno})` : "";
    errorBox.textContent = `${error.source}: ${error.type}: ${error.message}${where}`;
  }

  function renderSpeed() {
    const ms = model.get("interval_ms");
    speed.value = String(intervalToSlider(ms));
    const perSecond = 1000 / ms;
    speedLabel.textContent = perSecond >= 10 ? `${Math.round(perSecond)} steps/s` : `${perSecond.toFixed(1)} steps/s`;
  }

  function applyHeight() {
    const h = model.get("height");
    main.style.maxHeight = h > 0 ? `${h}px` : "";
    main.classList.toggle("sv-capped", h > 0);
  }

  // `step` reaches Python while playing and scrubbing too, so other widgets
  // can follow along. model.set() is local; only save_changes() is throttled.
  let syncTimer = null;
  let syncPending = false;

  function flushSync() {
    if (syncTimer !== null) clearTimeout(syncTimer);
    syncTimer = null;
    syncPending = false;
    model.save_changes();
  }

  function commitStep({ now = false } = {}) {
    if (model.get("step") !== cur) {
      model.set("step", cur);
      syncPending = true;
    }
    const ms = model.get("sync_throttle_ms");
    if (now || ms <= 0) {
      if (syncPending) flushSync();
      return;
    }
    // A trailing flush makes sure the last step of a burst isn't dropped.
    if (syncPending && syncTimer === null) {
      syncTimer = setTimeout(() => {
        syncTimer = null;
        if (syncPending) flushSync();
      }, ms);
    }
  }

  function goTo(index) {
    cur = clamp(index);
    renderStep();
    commitStep({ now: rafId === null });
  }

  function frame(time) {
    if (!lastTime) lastTime = time;
    pending += (time - lastTime) / model.get("interval_ms");
    lastTime = time;
    const advance = Math.floor(pending);
    if (advance > 0) {
      pending -= advance;
      let next = cur + advance;
      if (next > maxIndex()) {
        if (model.get("loop")) {
          next = next % (maxIndex() + 1);
        } else {
          cur = maxIndex();
          renderStep();
          stopPlaying();
          return;
        }
      }
      cur = next;
      renderStep();
      commitStep();
    }
    rafId = requestAnimationFrame(frame);
  }

  function startPlaying() {
    if (rafId !== null) return;
    if (cur >= maxIndex()) cur = 0;
    lastTime = 0;
    pending = 1; // show the next step immediately
    rafId = requestAnimationFrame(frame);
    playBtn.innerHTML = PAUSE_ICON;
    if (!model.get("playing")) {
      model.set("playing", true);
      model.save_changes();
    }
  }

  function stopPlaying() {
    if (rafId !== null) cancelAnimationFrame(rafId);
    rafId = null;
    playBtn.innerHTML = PLAY_ICON;
    model.set("playing", false);
    model.set("step", cur);
    flushSync();
  }

  const togglePlay = () => (rafId === null ? startPlaying() : stopPlaying());

  playBtn.addEventListener("click", togglePlay);
  prevBtn.addEventListener("click", () => goTo(cur - 1));
  nextBtn.addEventListener("click", () => goTo(cur + 1));

  speed.addEventListener("input", () => {
    model.set("interval_ms", Math.max(1, Math.round(sliderToInterval(Number(speed.value)))));
    model.save_changes();
  });

  function scrubTo(event) {
    const rect = timeline.getBoundingClientRect();
    const fraction = (event.clientX - rect.left) / Math.max(1, rect.width);
    cur = clamp(Math.floor(fraction * steps().length));
    renderStep();
    if (rafId === null) commitStep();
  }
  timeline.addEventListener("pointerdown", (event) => {
    timeline.setPointerCapture(event.pointerId);
    scrubTo(event);
  });
  timeline.addEventListener("pointermove", (event) => {
    if (timeline.hasPointerCapture(event.pointerId)) scrubTo(event);
  });
  timeline.addEventListener("pointerup", () => {
    if (rafId === null) commitStep({ now: true });
  });

  root.addEventListener("keydown", (event) => {
    const jump = event.shiftKey ? 10 : 1;
    if (event.key === "ArrowRight") goTo(cur + jump);
    else if (event.key === "ArrowLeft") goTo(cur - jump);
    else if (event.key === "Home") goTo(0);
    else if (event.key === "End") goTo(maxIndex());
    else if (event.key === " ") togglePlay();
    else return;
    event.preventDefault();
  });

  model.on("change:step", () => {
    if (model.get("step") !== cur) goTo(model.get("step"));
  });
  model.on("change:playing", () => {
    if (model.get("playing") && rafId === null) startPlaying();
    if (!model.get("playing") && rafId !== null) stopPlaying();
  });
  model.on("change:interval_ms", renderSpeed);
  model.on("change:height", applyHeight);
  model.on("change:error", renderError);
  model.on("change:lines", () => {
    buildCode();
    renderStep();
  });
  model.on("change:variables", renderStep);
  model.on("change:timeline_label", () => {
    buildTimeline();
    renderStep();
  });
  model.on("change:steps", () => {
    minViewWidth = 0;
    minViewHeight = 0;
    view.dataset.index = "";
    buildTimeline();
    renderStep();
  });

  buildCode();
  buildTimeline();
  applyHeight();
  renderSpeed();
  renderError();
  cur = clamp(model.get("step"));
  renderStep();
  if (model.get("playing")) startPlaying();

  return () => {
    if (rafId !== null) cancelAnimationFrame(rafId);
    if (syncTimer !== null) clearTimeout(syncTimer);
  };
}

export default { render };
