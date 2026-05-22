import { drag } from "d3-drag";
import { scaleLinear } from "d3-scale";
import { pointer, select } from "d3-selection";
import {
  curveBasis,
  curveBasisClosed,
  curveBumpX,
  curveCardinal,
  curveCardinalClosed,
  curveCatmullRom,
  curveCatmullRomClosed,
  curveLinear,
  curveLinearClosed,
  curveMonotoneX,
  curveNatural,
  curveStep,
  curveStepAfter,
  curveStepBefore,
  line,
} from "d3-shape";

const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';
const MARGIN = { top: 18, right: 18, bottom: 18, left: 18 };
const CURVE_OPTIONS = [
  ["linear", "Linear"],
  ["step", "Step"],
  ["step_before", "Step before"],
  ["step_after", "Step after"],
  ["basis", "Basis"],
  ["natural", "Natural"],
  ["cardinal", "Cardinal"],
  ["catmull_rom", "Catmull-Rom"],
  ["monotone_x", "Monotone X"],
  ["bump_x", "Bump X"],
];

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value)));
}

function coercePoint(point) {
  return {
    x: Number(point?.x ?? 0),
    y: Number(point?.y ?? 0),
  };
}

function sortPoints(points) {
  return points
    .map((point, index) => ({ ...coercePoint(point), __index: index }))
    .sort((a, b) => a.x - b.x || a.__index - b.__index)
    .map(({ __index, ...point }) => point);
}

function orderedPoints(points, closed = false) {
  if (closed) {
    return points.map(coercePoint);
  }
  return sortPoints(points);
}

function effectivePoints(points, closed, curveName) {
  if (closed && points.length > 0 && !hasClosedCurve(curveName)) {
    return [...points, { ...points[0] }];
  }
  return points;
}

function hasClosedCurve(name) {
  return ["linear", "basis", "natural", "cardinal", "catmull_rom"].includes(name);
}

function curveFactory(name, model, closed = false) {
  if (closed) {
    if (name === "linear") return curveLinearClosed;
    if (name === "basis" || name === "natural") return curveBasisClosed;
    if (name === "cardinal") {
      return curveCardinalClosed.tension(clamp01(model.get("tension")));
    }
    if (name === "catmull_rom") {
      return curveCatmullRomClosed.alpha(clamp01(model.get("alpha")));
    }
  }
  if (name === "step") return curveStep;
  if (name === "step_before") return curveStepBefore;
  if (name === "step_after") return curveStepAfter;
  if (name === "basis") return curveBasis;
  if (name === "natural") return curveNatural;
  if (name === "cardinal") return curveCardinal.tension(clamp01(model.get("tension")));
  if (name === "catmull_rom") return curveCatmullRom.alpha(clamp01(model.get("alpha")));
  if (name === "monotone_x") return curveMonotoneX;
  if (name === "bump_x") return curveBumpX;
  return curveLinear;
}

function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.className = "curve-editor-wrapper";

  const controls = document.createElement("div");
  controls.className = "curve-editor-controls";

  const curveLabel = document.createElement("label");
  curveLabel.className = "curve-editor-field";
  const curveLabelText = document.createElement("span");
  curveLabelText.textContent = "curve";
  const curveSelect = document.createElement("select");
  curveSelect.className = "curve-editor-select";
  curveSelect.name = "curve";
  curveSelect.setAttribute("aria-label", "Curve interpolation");
  CURVE_OPTIONS.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    curveSelect.appendChild(option);
  });
  curveLabel.append(curveLabelText, curveSelect);

  const tensionLabel = document.createElement("label");
  tensionLabel.className = "curve-editor-field curve-editor-parameter";
  const tensionText = document.createElement("span");
  tensionText.textContent = "tension";
  const tensionInput = document.createElement("input");
  tensionInput.className = "curve-editor-range curve-editor-small-range";
  tensionInput.name = "tension";
  tensionInput.type = "range";
  tensionInput.min = "0";
  tensionInput.max = "1";
  tensionInput.step = "0.01";
  tensionInput.setAttribute("aria-label", "Cardinal tension");
  const tensionValue = document.createElement("span");
  tensionValue.className = "curve-editor-value";
  tensionLabel.append(tensionText, tensionInput, tensionValue);

  const alphaLabel = document.createElement("label");
  alphaLabel.className = "curve-editor-field curve-editor-parameter";
  const alphaText = document.createElement("span");
  alphaText.textContent = "alpha";
  const alphaInput = document.createElement("input");
  alphaInput.className = "curve-editor-range curve-editor-small-range";
  alphaInput.name = "alpha";
  alphaInput.type = "range";
  alphaInput.min = "0";
  alphaInput.max = "1";
  alphaInput.step = "0.01";
  alphaInput.setAttribute("aria-label", "Catmull-Rom alpha");
  const alphaValue = document.createElement("span");
  alphaValue.className = "curve-editor-value";
  alphaLabel.append(alphaText, alphaInput, alphaValue);

  controls.append(curveLabel, tensionLabel, alphaLabel);

  const svgNode = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svgNode.classList.add("curve-editor-svg");

  const timeline = document.createElement("div");
  timeline.className = "curve-editor-timeline";

  const playButton = document.createElement("button");
  playButton.className = "curve-editor-play";
  playButton.type = "button";
  playButton.setAttribute("aria-label", "Play or pause");

  const progressInput = document.createElement("input");
  progressInput.className = "curve-editor-range curve-editor-progress";
  progressInput.name = "t";
  progressInput.type = "range";
  progressInput.min = "0";
  progressInput.max = "1";
  progressInput.step = "0.001";
  progressInput.setAttribute("aria-label", "Curve progress");

  const readout = document.createElement("span");
  readout.className = "curve-editor-readout";

  const closedLabel = document.createElement("label");
  closedLabel.className = "curve-editor-check";
  const closedInput = document.createElement("input");
  closedInput.name = "closed";
  closedInput.type = "checkbox";
  closedInput.setAttribute("aria-label", "Close curve");
  closedLabel.append(closedInput, document.createTextNode("closed"));

  const loopLabel = document.createElement("label");
  loopLabel.className = "curve-editor-check";
  const loopInput = document.createElement("input");
  loopInput.name = "loop";
  loopInput.type = "checkbox";
  loopInput.setAttribute("aria-label", "Loop playback");
  loopLabel.append(loopInput, document.createTextNode("loop"));

  timeline.append(playButton, progressInput, readout, closedLabel, loopLabel);
  wrapper.append(controls, svgNode, timeline);
  el.appendChild(wrapper);

  const svg = select(svgNode);
  const gridGroup = svg.append("g").attr("class", "curve-editor-grid");
  const path = svg.append("path").attr("class", "curve-editor-path");
  const tracePath = svg.append("path").attr("class", "curve-editor-trace");
  const hitbox = svg.append("rect").attr("class", "curve-editor-hitbox");
  const currentPoint = svg.append("circle").attr("class", "curve-editor-current").attr("r", 5);
  const pointGroup = svg.append("g").attr("class", "curve-editor-points");

  let intervalId = null;
  let lastSync = 0;
  let renderedButtonPlaying = null;

  function width() {
    return model.get("width") || 600;
  }

  function height() {
    return model.get("height") || 360;
  }

  function innerWidth() {
    return Math.max(1, width() - MARGIN.left - MARGIN.right);
  }

  function innerHeight() {
    return Math.max(1, height() - MARGIN.top - MARGIN.bottom);
  }

  function bounds() {
    return {
      x: model.get("x_bounds") || [0, 1],
      y: model.get("y_bounds") || [0, 1],
    };
  }

  function points() {
    return orderedPoints(model.get("points") || [], model.get("closed"));
  }

  function pathPoints() {
    return effectivePoints(points(), model.get("closed"), model.get("curve"));
  }

  function scales() {
    const chartBounds = bounds();
    return {
      x: scaleLinear().domain(chartBounds.x).range([MARGIN.left, MARGIN.left + innerWidth()]),
      y: scaleLinear().domain(chartBounds.y).range([MARGIN.top + innerHeight(), MARGIN.top]),
    };
  }

  function xInvert(px) {
    const { x } = scales();
    const clamped = Math.max(MARGIN.left, Math.min(MARGIN.left + innerWidth(), px));
    return x.invert(clamped);
  }

  function yInvert(py) {
    const { y } = scales();
    const clamped = Math.max(MARGIN.top, Math.min(MARGIN.top + innerHeight(), py));
    return y.invert(clamped);
  }

  function selectedIndex() {
    const selected = model.get("selected_index");
    return Number.isInteger(selected) ? selected : -1;
  }

  function lineGenerator(xScale, yScale) {
    return line()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y))
      .curve(curveFactory(model.get("curve"), model, model.get("closed")));
  }

  function syncPoints(nextPoints, selectedPoint = null) {
    const sorted = orderedPoints(nextPoints, model.get("closed"));
    let nextSelected = -1;
    if (selectedPoint) {
      nextSelected = sorted.findIndex(
        (point) => point.x === selectedPoint.x && point.y === selectedPoint.y
      );
    }
    model.set("points", sorted);
    model.set("selected_index", nextSelected);
    model.save_changes();
  }

  function drawGrid(xScale, yScale) {
    const vertical = xScale.ticks(6).map((tick) => ({
      axis: "x",
      value: tick,
      x1: xScale(tick),
      x2: xScale(tick),
      y1: MARGIN.top,
      y2: MARGIN.top + innerHeight(),
    }));
    const horizontal = yScale.ticks(5).map((tick) => ({
      axis: "y",
      value: tick,
      x1: MARGIN.left,
      x2: MARGIN.left + innerWidth(),
      y1: yScale(tick),
      y2: yScale(tick),
    }));

    gridGroup.selectAll("line")
      .data([...vertical, ...horizontal], (d) => `${d.axis}-${d.value}`)
      .join("line")
      .attr("x1", (d) => d.x1)
      .attr("x2", (d) => d.x2)
      .attr("y1", (d) => d.y1)
      .attr("y2", (d) => d.y2);
  }

  function syncSliderFill(input, value) {
    const pct = clamp01(value) * 100;
    const fill = getComputedStyle(wrapper).getPropertyValue("--curve-editor-accent").trim();
    const track = getComputedStyle(wrapper).getPropertyValue("--curve-editor-track").trim();
    input.style.background = `linear-gradient(to right, ${fill} ${pct}%, ${track} ${pct}%)`;
  }

  function renderButton() {
    const playing = intervalId !== null || Boolean(model.get("playing"));
    if (renderedButtonPlaying !== playing) {
      playButton.innerHTML = playing ? PAUSE_ICON : PLAY_ICON;
      renderedButtonPlaying = playing;
    }
    playButton.setAttribute("aria-label", playing ? "Pause" : "Play");
    playButton.setAttribute("aria-pressed", playing ? "true" : "false");
  }

  function renderControls() {
    const curve = model.get("curve") || "natural";
    const tension = clamp01(model.get("tension"));
    const alpha = clamp01(model.get("alpha"));
    const t = clamp01(model.get("t"));

    curveSelect.value = curve;
    tensionInput.value = String(tension);
    alphaInput.value = String(alpha);
    progressInput.value = String(t);
    closedInput.checked = Boolean(model.get("closed"));
    loopInput.checked = Boolean(model.get("loop"));
    tensionValue.textContent = tension.toFixed(2);
    alphaValue.textContent = alpha.toFixed(2);
    readout.textContent = t.toFixed(3);
    syncSliderFill(tensionInput, tension);
    syncSliderFill(alphaInput, alpha);
    syncSliderFill(progressInput, t);
    renderButton();

    tensionLabel.hidden = curve !== "cardinal";
    alphaLabel.hidden = curve !== "catmull_rom";
  }

  function syncCurrent(force = false) {
    const node = path.node();
    if (!node) return;

    let length = 0;
    try {
      length = node.getTotalLength();
    } catch {
      return;
    }
    if (!Number.isFinite(length) || length <= 0) return;

    const now = performance.now();
    const throttle = model.get("sync_throttle_ms") ?? 250;
    const point = node.getPointAtLength(length * clamp01(model.get("t")));
    const nextX = xInvert(point.x);
    const nextY = yInvert(point.y);

    currentPoint
      .attr("cx", point.x)
      .attr("cy", point.y)
      .attr("display", null);

    if (!force && throttle > 0 && now - lastSync < throttle) return;

    model.set("x", nextX);
    model.set("y", nextY);
    model.save_changes();
    lastSync = now;
  }

  function renderFrame(sync = true) {
    const w = width();
    const h = height();
    const pts = points();
    const effective = pathPoints();
    const { x, y } = scales();
    const generator = lineGenerator(x, y);

    wrapper.style.width = `${w}px`;
    svg
      .attr("viewBox", `0 0 ${w} ${h}`)
      .attr("width", "100%")
      .attr("height", "auto")
      .style("aspect-ratio", `${w} / ${h}`);

    renderControls();
    drawGrid(x, y);

    hitbox
      .attr("x", MARGIN.left)
      .attr("y", MARGIN.top)
      .attr("width", innerWidth())
      .attr("height", innerHeight());

    path.attr("d", effective.length >= 2 ? generator(effective) : "");

    if (effective.length >= 2) {
      try {
        const traceNode = path.node();
        const traceLength = traceNode.getTotalLength();
        const t = clamp01(model.get("t"));
        const dash = traceLength * t;
        tracePath
          .attr("d", path.attr("d"))
          .attr("stroke-dasharray", `${dash} ${Math.max(0, traceLength - dash)}`);
      } catch {
        tracePath.attr("d", "");
        currentPoint.attr("display", "none");
      }
    } else {
      tracePath.attr("d", "");
      currentPoint.attr("display", "none");
    }

    pointGroup.selectAll("circle")
      .data(pts)
      .join("circle")
      .attr("class", (_, index) => (
        index === selectedIndex()
          ? "curve-editor-point is-selected"
          : "curve-editor-point"
      ))
      .attr("r", 6)
      .attr("cx", (d) => x(d.x))
      .attr("cy", (d) => y(d.y))
      .on("click", (event, d) => {
        event.stopPropagation();
        model.set("selected_index", pts.indexOf(d));
        model.save_changes();
        renderFrame(false);
      })
      .on("dblclick", (event, d) => {
        event.stopPropagation();
        stopPlaying();
        if (pts.length <= 2) return;
        const next = pts.filter((point) => point !== d);
        syncPoints(next, null);
        renderFrame(true);
      })
      .call(drag()
        .on("start", function (event, d) {
          stopPlaying();
          select(this).classed("is-dragging", true);
          model.set("selected_index", pts.indexOf(d));
          model.save_changes();
        })
        .on("drag", function (event, d) {
          const [px, py] = pointer(event.sourceEvent || event, svgNode);
          d.x = xInvert(px);
          d.y = yInvert(py);
          const next = pts.map((point) => (
            point === d ? { x: d.x, y: d.y } : { x: point.x, y: point.y }
          ));
          syncPoints(next, d);
          renderFrame(true);
        })
        .on("end", function () {
          select(this).classed("is-dragging", false);
        }));

    if (sync) syncCurrent(true);
  }

  function setT(value, forceSync = false) {
    model.set("t", clamp01(value));
    renderFrame(false);
    syncCurrent(forceSync);
  }

  function startTimer() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
    intervalId = setInterval(() => {
      const duration = model.get("duration_ms") || 12000;
      const next = model.get("t") + model.get("interval_ms") / duration;
      if (next >= 1) {
        if (model.get("loop")) {
          setT(0, true);
        } else {
          setT(1, true);
          stopPlaying();
        }
      } else {
        setT(next, false);
      }
    }, model.get("interval_ms"));
    renderButton();
  }

  function stopTimer() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
    renderButton();
  }

  function setPlayingTrait(value) {
    if (model.get("playing") === value) return;
    model.set("playing", value);
    model.save_changes();
  }

  function startPlaying() {
    setPlayingTrait(true);
    if (intervalId === null) startTimer();
    renderButton();
  }

  function stopPlaying() {
    setPlayingTrait(false);
    stopTimer();
    renderButton();
  }

  curveSelect.addEventListener("change", () => {
    model.set("curve", curveSelect.value);
    model.save_changes();
    renderFrame(true);
  });

  tensionInput.addEventListener("input", () => {
    model.set("tension", clamp01(tensionInput.value));
    model.save_changes();
    renderFrame(true);
  });

  alphaInput.addEventListener("input", () => {
    model.set("alpha", clamp01(alphaInput.value));
    model.save_changes();
    renderFrame(true);
  });

  playButton.addEventListener("click", () => {
    if (intervalId !== null) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

  progressInput.addEventListener("input", () => {
    stopPlaying();
    setT(Number(progressInput.value), true);
    model.save_changes();
  });

  closedInput.addEventListener("change", () => {
    stopPlaying();
    const currentPoints = points();
    const selectedPoint = currentPoints[selectedIndex()] ?? null;
    model.set("closed", closedInput.checked);
    if (closedInput.checked) {
      model.save_changes();
    } else {
      syncPoints(currentPoints, selectedPoint);
    }
    renderFrame(true);
  });

  loopInput.addEventListener("change", () => {
    model.set("loop", loopInput.checked);
    model.save_changes();
    renderControls();
  });

  svg.on("click", () => {
    model.set("selected_index", -1);
    model.save_changes();
    renderFrame(false);
  });

  svg.on("dblclick", (event) => {
    if (event.target?.classList?.contains("curve-editor-point")) return;
    stopPlaying();
    const [px, py] = pointer(event, svgNode);
    const added = { x: xInvert(px), y: yInvert(py) };
    syncPoints([...points(), added], added);
    renderFrame(true);
  });

  model.on("change:playing", () => {
    const playing = model.get("playing");
    if (playing) {
      startTimer();
    } else {
      stopTimer();
    }
    renderButton();
  });

  model.on("change:interval_ms", () => {
    if (intervalId !== null) {
      startTimer();
    }
  });

  [
    "points",
    "curve",
    "tension",
    "alpha",
    "closed",
    "width",
    "height",
    "x_bounds",
    "y_bounds",
  ].forEach((name) => {
    model.on(`change:${name}`, () => renderFrame(true));
  });

  model.on("change:t", () => {
    renderFrame(false);
    syncCurrent(true);
  });
  model.on("change:loop", renderControls);
  model.on("change:selected_index", () => renderFrame(false));

  renderFrame(true);
  if (model.get("playing")) startPlaying();

  return () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };
}

export default { render };
