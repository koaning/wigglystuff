import { pointer, select } from "d3-selection";
import { drag } from "d3-drag";

const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';
const MARGIN_TIGHT = { top: 24, right: 24, bottom: 24, left: 24 };
const MARGIN_WITH_AXES = { top: 12, right: 16, bottom: 32, left: 44 };
const TICK_LENGTH = 5;
const SAMPLE_COUNT = 120;

function niceTicks(min, max, count = 5) {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [];
  const range = max - min;
  const rough = range / Math.max(1, count);
  const exp = Math.floor(Math.log10(rough));
  const base = Math.pow(10, exp);
  const candidates = [1, 2, 2.5, 5, 10].map((mult) => mult * base);
  const step = candidates.find((value) => range / value <= count * 1.5) ?? candidates[candidates.length - 1];
  const ticks = [];
  const start = Math.ceil(min / step) * step;
  for (let value = start; value <= max + step * 1e-9; value += step) {
    ticks.push(Number((Math.round(value / step) * step).toFixed(12)));
  }
  return ticks;
}

function formatTick(value) {
  if (!Number.isFinite(value)) return "";
  if (value === 0) return "0";
  const abs = Math.abs(value);
  if (abs >= 1000 || abs < 0.01) return value.toExponential(1).replace("e+", "e");
  const fixed = value.toFixed(3);
  return fixed.replace(/\.?0+$/, "");
}

function clamp01(value) {
  return Math.max(0, Math.min(1, Number(value)));
}

function coercePoint(point) {
  return {
    x: Number(point?.x ?? 0),
    y: Number(point?.y ?? 0),
  };
}

function effectivePoints(points, closed) {
  if (closed && points.length > 0) {
    return [...points, { ...points[0] }];
  }
  return points;
}

function deCasteljau(points, t) {
  if (!points.length) return { x: NaN, y: NaN };
  let level = points.map((point) => ({ ...point }));
  const amount = clamp01(t);
  while (level.length > 1) {
    level = level.slice(0, -1).map((point, index) => {
      const next = level[index + 1];
      return {
        x: point.x + (next.x - point.x) * amount,
        y: point.y + (next.y - point.y) * amount,
      };
    });
  }
  return level[0];
}

function pathFromPixels(points, xScale, yScale) {
  if (!points.length) return "";
  const [first, ...rest] = points;
  return [
    `M${xScale(first.x)},${yScale(first.y)}`,
    ...rest.map((point) => `L${xScale(point.x)},${yScale(point.y)}`),
  ].join("");
}

function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.className = "bezier-curve-wrapper";

  const svgNode = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svgNode.classList.add("bezier-curve-svg");

  const controls = document.createElement("div");
  controls.className = "bezier-curve-controls";

  const playButton = document.createElement("button");
  playButton.className = "bezier-curve-play";
  playButton.type = "button";
  playButton.setAttribute("aria-label", "Play or pause");

  const slider = document.createElement("input");
  slider.className = "bezier-curve-range";
  slider.type = "range";
  slider.min = "0";
  slider.max = "1";
  slider.step = "0.001";
  slider.setAttribute("aria-label", "Bezier parameter t");

  const readout = document.createElement("span");
  readout.className = "bezier-curve-readout";

  const closedLabel = document.createElement("label");
  closedLabel.className = "bezier-curve-check";
  const closedInput = document.createElement("input");
  closedInput.type = "checkbox";
  closedInput.setAttribute("aria-label", "Close curve");
  closedLabel.append(closedInput, document.createTextNode("closed"));

  const loopLabel = document.createElement("label");
  loopLabel.className = "bezier-curve-check";
  const loopInput = document.createElement("input");
  loopInput.type = "checkbox";
  loopInput.setAttribute("aria-label", "Loop playback");
  loopLabel.append(loopInput, document.createTextNode("loop"));

  controls.append(playButton, slider, readout, closedLabel, loopLabel);
  wrapper.append(svgNode, controls);
  el.appendChild(wrapper);

  const svg = select(svgNode);
  const clipId = `bezier-clip-${Math.random().toString(36).slice(2)}`;
  const clipRect = svg.append("defs")
    .append("clipPath").attr("id", clipId)
    .append("rect");
  const gridGroup = svg.append("g")
    .attr("class", "bezier-curve-grid")
    .attr("clip-path", `url(#${clipId})`);
  const axisGroup = svg.append("g").attr("class", "bezier-curve-axis");
  const plotGroup = svg.append("g")
    .attr("class", "bezier-curve-plot")
    .attr("clip-path", `url(#${clipId})`);
  const controlPath = plotGroup.append("path").attr("class", "bezier-curve-control-path");
  const curvePath = plotGroup.append("path").attr("class", "bezier-curve-path");
  const tracePath = plotGroup.append("path").attr("class", "bezier-curve-trace");
  const constructionGroup = plotGroup.append("g").attr("class", "bezier-curve-construction");
  const currentPoint = plotGroup.append("circle").attr("class", "bezier-curve-current").attr("r", 5);
  const pointGroup = plotGroup.append("g").attr("class", "bezier-curve-points");

  let intervalId = null;
  let lastSync = 0;
  let lastSampleSync = 0;
  let renderedButtonPlaying = null;
  const view = { tx: 0, ty: 0, k: 1 };

  function svgPointer(event) {
    return pointer(event.sourceEvent || event, svgNode);
  }

  function width() {
    return model.get("width") || 600;
  }

  function height() {
    return model.get("height") || 360;
  }

  function bounds() {
    return {
      x: model.get("x_bounds") || [0, 1],
      y: model.get("y_bounds") || [0, 1],
    };
  }

  function margins() {
    return model.get("show_axes") ? MARGIN_WITH_AXES : MARGIN_TIGHT;
  }

  function points() {
    return (model.get("points") || []).map(coercePoint);
  }

  function baseXScale(value) {
    const [min, max] = bounds().x;
    const m = margins();
    return m.left + ((value - min) / (max - min)) * (width() - m.left - m.right);
  }

  function baseYScale(value) {
    const [min, max] = bounds().y;
    const m = margins();
    return m.top + ((max - value) / (max - min)) * (height() - m.top - m.bottom);
  }

  function xScale(value) {
    return view.tx + view.k * baseXScale(value);
  }

  function yScale(value) {
    return view.ty + view.k * baseYScale(value);
  }

  function xInvert(px) {
    const [min, max] = bounds().x;
    const m = margins();
    const ux = (px - view.tx) / view.k;
    return min + ((ux - m.left) / (width() - m.left - m.right)) * (max - min);
  }

  function yInvert(py) {
    const [min, max] = bounds().y;
    const m = margins();
    const uy = (py - view.ty) / view.k;
    return max - ((uy - m.top) / (height() - m.top - m.bottom)) * (max - min);
  }

  function visibleBounds() {
    const m = margins();
    const w = width();
    const h = height();
    return {
      x: [xInvert(m.left), xInvert(w - m.right)],
      y: [yInvert(h - m.bottom), yInvert(m.top)],
    };
  }

  function sampled(amount = 1) {
    const pts = effectivePoints(points(), model.get("closed"));
    if (!pts.length) return [];
    const count = Math.max(2, Math.ceil(SAMPLE_COUNT * clamp01(amount)));
    return Array.from({ length: count }, (_, index) => {
      const t = amount * (index / (count - 1));
      return deCasteljau(pts, t);
    });
  }

  function constructionLevels() {
    const pts = effectivePoints(points(), model.get("closed"));
    const levels = [];
    let level = pts.map((point) => ({ ...point }));
    const amount = clamp01(model.get("t"));
    while (level.length > 1) {
      level = level.slice(0, -1).map((point, index) => {
        const next = level[index + 1];
        return {
          x: point.x + (next.x - point.x) * amount,
          y: point.y + (next.y - point.y) * amount,
        };
      });
      levels.push(level);
    }
    return levels;
  }

  function syncCurrent(force = false) {
    const now = performance.now();
    const throttle = model.get("sync_throttle_ms") ?? 100;
    if (!force && throttle > 0 && now - lastSync < throttle) return;

    const p = deCasteljau(effectivePoints(points(), model.get("closed")), model.get("t"));
    model.set("x", p.x);
    model.set("y", p.y);
    model.save_changes();
    lastSync = now;
  }

  function syncSamples(force = false) {
    const now = performance.now();
    const throttle = model.get("sync_throttle_ms") ?? 100;
    if (!force && throttle > 0 && now - lastSampleSync < throttle) return;

    const pts = effectivePoints(points(), model.get("closed"));
    if (!pts.length) {
      model.set("samples", []);
      model.save_changes();
      lastSampleSync = now;
      return;
    }
    const n = Math.max(2, Number(model.get("n_samples")) || 100);
    const samples = new Array(n);
    for (let i = 0; i < n; i++) {
      const p = deCasteljau(pts, i / (n - 1));
      samples[i] = { x: p.x, y: p.y };
    }
    model.set("samples", samples);
    model.save_changes();
    lastSampleSync = now;
  }

  function setT(value, forceSync = false) {
    model.set("t", clamp01(value));
    syncCurrent(forceSync);
    renderFrame();
  }

  function syncSliderFill() {
    const pct = clamp01(model.get("t")) * 100;
    const fill = getComputedStyle(wrapper).getPropertyValue("--bezier-accent").trim();
    const track = getComputedStyle(wrapper).getPropertyValue("--bezier-track").trim();
    slider.style.background = `linear-gradient(to right, ${fill} ${pct}%, ${track} ${pct}%)`;
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

  function drawAxes() {
    if (!model.get("show_axes")) {
      axisGroup.selectAll("*").remove();
      return;
    }
    const w = width();
    const h = height();
    const m = margins();
    const { x: xb, y: yb } = visibleBounds();
    const xPxMin = m.left;
    const xPxMax = w - m.right;
    const yPxMin = m.top;
    const yPxMax = h - m.bottom;
    const xTicks = niceTicks(xb[0], xb[1], 5)
      .filter((d) => xScale(d) >= xPxMin - 0.5 && xScale(d) <= xPxMax + 0.5);
    const yTicks = niceTicks(yb[0], yb[1], 5)
      .filter((d) => yScale(d) >= yPxMin - 0.5 && yScale(d) <= yPxMax + 0.5);

    const baseY = h - m.bottom;
    const baseX = m.left;

    axisGroup.selectAll("*").remove();

    const xGroup = axisGroup.append("g").attr("class", "bezier-curve-axis-x");
    xGroup.append("line")
      .attr("class", "bezier-curve-axis-domain")
      .attr("x1", m.left).attr("x2", w - m.right)
      .attr("y1", baseY).attr("y2", baseY);
    const xTick = xGroup.selectAll("g.tick")
      .data(xTicks)
      .join("g")
      .attr("class", "tick")
      .attr("transform", (d) => `translate(${xScale(d)},${baseY})`);
    xTick.append("line").attr("y2", TICK_LENGTH);
    xTick.append("text")
      .attr("y", TICK_LENGTH + 10)
      .attr("text-anchor", "middle")
      .text((d) => formatTick(d));

    const yGroup = axisGroup.append("g").attr("class", "bezier-curve-axis-y");
    yGroup.append("line")
      .attr("class", "bezier-curve-axis-domain")
      .attr("x1", baseX).attr("x2", baseX)
      .attr("y1", m.top).attr("y2", h - m.bottom);
    const yTick = yGroup.selectAll("g.tick")
      .data(yTicks)
      .join("g")
      .attr("class", "tick")
      .attr("transform", (d) => `translate(${baseX},${yScale(d)})`);
    yTick.append("line").attr("x2", -TICK_LENGTH);
    yTick.append("text")
      .attr("x", -TICK_LENGTH - 4)
      .attr("dy", "0.32em")
      .attr("text-anchor", "end")
      .text((d) => formatTick(d));
  }

  function drawGrid() {
    if (!model.get("show_axes")) {
      gridGroup.selectAll("*").remove();
      return;
    }
    const w = width();
    const h = height();
    const m = margins();
    const { x: xb, y: yb } = visibleBounds();
    const xPxMin = m.left;
    const xPxMax = w - m.right;
    const yPxMin = m.top;
    const yPxMax = h - m.bottom;
    const xTicks = niceTicks(xb[0], xb[1], 5)
      .filter((d) => xScale(d) >= xPxMin - 0.5 && xScale(d) <= xPxMax + 0.5);
    const yTicks = niceTicks(yb[0], yb[1], 5)
      .filter((d) => yScale(d) >= yPxMin - 0.5 && yScale(d) <= yPxMax + 0.5);

    gridGroup.selectAll("line.bezier-curve-grid-x")
      .data(xTicks)
      .join("line")
      .attr("class", "bezier-curve-grid-x")
      .attr("x1", (d) => xScale(d))
      .attr("x2", (d) => xScale(d))
      .attr("y1", yPxMin)
      .attr("y2", yPxMax);

    gridGroup.selectAll("line.bezier-curve-grid-y")
      .data(yTicks)
      .join("line")
      .attr("class", "bezier-curve-grid-y")
      .attr("x1", xPxMin)
      .attr("x2", xPxMax)
      .attr("y1", (d) => yScale(d))
      .attr("y2", (d) => yScale(d));
  }

  function renderFrame() {
    const w = width();
    const h = height();
    const pts = points();
    const effective = effectivePoints(pts, model.get("closed"));
    const t = clamp01(model.get("t"));
    const current = deCasteljau(effective, t);

    wrapper.style.width = `${w}px`;
    svg
      .attr("viewBox", `0 0 ${w} ${h}`)
      .attr("width", "100%")
      .attr("height", "auto")
      .style("aspect-ratio", `${w} / ${h}`);

    slider.value = String(t);
    closedInput.checked = Boolean(model.get("closed"));
    loopInput.checked = Boolean(model.get("loop"));
    readout.textContent = t.toFixed(3);
    syncSliderFill();
    renderButton();

    const m = margins();
    clipRect
      .attr("x", m.left)
      .attr("y", m.top)
      .attr("width", Math.max(0, w - m.left - m.right))
      .attr("height", Math.max(0, h - m.top - m.bottom));

    drawGrid();
    drawAxes();
    controlPath.attr("d", pathFromPixels(effective, xScale, yScale));
    curvePath.attr("d", pathFromPixels(sampled(1), xScale, yScale));
    tracePath.attr("d", pathFromPixels(sampled(t), xScale, yScale));

    const levelLines = constructionLevels().flatMap((level, levelIndex) => {
      const lines = level.slice(0, -1).map((point, index) => ({
        levelIndex,
        a: point,
        b: level[index + 1],
      }));
      if (model.get("closed") && levelIndex === 0 && level.length > 2) {
        lines.push({
          levelIndex,
          a: level[level.length - 1],
          b: level[0],
        });
      }
      return lines;
    });

    constructionGroup.selectAll("line")
      .data(levelLines)
      .join("line")
      .attr("x1", (d) => xScale(d.a.x))
      .attr("y1", (d) => yScale(d.a.y))
      .attr("x2", (d) => xScale(d.b.x))
      .attr("y2", (d) => yScale(d.b.y))
      .attr("opacity", (d) => Math.max(0.2, 0.8 - d.levelIndex * 0.14));

    currentPoint
      .attr("cx", xScale(current.x))
      .attr("cy", yScale(current.y))
      .attr("display", Number.isFinite(current.x) && Number.isFinite(current.y) ? null : "none");

    pointGroup.selectAll("circle")
      .data(pts)
      .join("circle")
      .attr("class", "bezier-curve-point")
      .attr("r", 7)
      .attr("cx", (d) => xScale(d.x))
      .attr("cy", (d) => yScale(d.y))
      .on("dblclick", (event, d) => {
        event.stopPropagation();
        stopPlaying();
        const next = pts
          .filter((point) => point !== d)
          .map((point) => ({ x: point.x, y: point.y }));
        model.set("points", next);
        syncCurrent(true);
        syncSamples(true);
        model.save_changes();
        renderFrame();
      })
      .call(drag()
        .on("start", function () {
          stopPlaying();
          select(this).classed("is-dragging", true);
        })
        .on("drag", function (event, d) {
          const [px, py] = svgPointer(event);
          d.x = xInvert(px);
          d.y = yInvert(py);
          const next = pts.map((point) => ({ x: point.x, y: point.y }));
          model.set("points", next);
          syncCurrent(true);
          syncSamples(false);
          renderFrame();
        })
        .on("end", function () {
          select(this).classed("is-dragging", false);
          syncSamples(true);
          model.save_changes();
        }));
  }

  function startPlaying() {
    if (intervalId !== null) return;
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
    model.set("playing", true);
    model.save_changes();
    renderButton();
  }

  function stopPlaying() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
    model.set("playing", false);
    model.save_changes();
    renderButton();
  }

  playButton.addEventListener("click", () => {
    if (intervalId !== null) {
      stopPlaying();
    } else {
      startPlaying();
    }
  });

  slider.addEventListener("input", () => {
    stopPlaying();
    setT(Number(slider.value), true);
    model.save_changes();
  });

  closedInput.addEventListener("change", () => {
    model.set("closed", closedInput.checked);
    syncCurrent(true);
    syncSamples(true);
    model.save_changes();
    renderFrame();
  });

  loopInput.addEventListener("change", () => {
    model.set("loop", loopInput.checked);
    model.save_changes();
  });

  svg.on("dblclick", (event) => {
    if (event.target?.classList?.contains("bezier-curve-point")) return;
    const [px, py] = pointer(event, svgNode);
    const next = [...points(), { x: xInvert(px), y: yInvert(py) }];
    model.set("points", next);
    syncCurrent(true);
    syncSamples(true);
    model.save_changes();
    renderFrame();
  });

  svgNode.addEventListener("wheel", (event) => {
    event.preventDefault();
    const [px, py] = pointer(event, svgNode);
    const factor = Math.exp(-event.deltaY * 0.001);
    const newK = Math.max(0.1, Math.min(50, view.k * factor));
    const ratio = newK / view.k;
    view.tx = px - (px - view.tx) * ratio;
    view.ty = py - (py - view.ty) * ratio;
    view.k = newK;
    renderFrame();
  }, { passive: false });

  let panPointerId = null;
  let panLast = null;
  svgNode.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    if (event.target?.classList?.contains("bezier-curve-point")) return;
    panPointerId = event.pointerId;
    panLast = pointer(event, svgNode);
    svgNode.setPointerCapture(panPointerId);
    svgNode.classList.add("is-panning");
  });
  svgNode.addEventListener("pointermove", (event) => {
    if (panPointerId === null || event.pointerId !== panPointerId) return;
    const [px, py] = pointer(event, svgNode);
    view.tx += px - panLast[0];
    view.ty += py - panLast[1];
    panLast = [px, py];
    renderFrame();
  });
  const endPan = (event) => {
    if (panPointerId === null || event.pointerId !== panPointerId) return;
    try { svgNode.releasePointerCapture(panPointerId); } catch (_) {}
    panPointerId = null;
    panLast = null;
    svgNode.classList.remove("is-panning");
  };
  svgNode.addEventListener("pointerup", endPan);
  svgNode.addEventListener("pointercancel", endPan);

  model.on("change:playing", () => {
    const playing = model.get("playing");
    if (playing && intervalId === null) {
      startPlaying();
    } else if (!playing && intervalId !== null) {
      stopPlaying();
    }
    renderButton();
  });

  model.on("change:interval_ms", () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
      if (model.get("playing")) startPlaying();
    }
  });

  [
    "points",
    "t",
    "closed",
    "loop",
    "width",
    "height",
    "x_bounds",
    "y_bounds",
  ].forEach((name) => {
    model.on(`change:${name}`, () => {
      if (name !== "loop") syncCurrent(name !== "t");
      if (name !== "t" && name !== "loop") syncSamples(true);
      renderFrame();
    });
  });

  model.on("change:show_axes", renderFrame);
  model.on("change:n_samples", () => syncSamples(true));

  renderFrame();
  syncCurrent(true);
  syncSamples(true);
  if (model.get("playing")) startPlaying();

  return () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };
}

export default { render };
