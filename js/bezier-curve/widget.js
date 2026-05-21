import { pointer, select } from "d3-selection";
import { drag } from "d3-drag";

const PLAY_ICON = '<svg viewBox="0 0 16 16"><polygon points="4,2 14,8 4,14"/></svg>';
const PAUSE_ICON = '<svg viewBox="0 0 16 16"><rect x="3" y="2" width="4" height="12"/><rect x="9" y="2" width="4" height="12"/></svg>';
const MARGIN = 24;
const SAMPLE_COUNT = 120;

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
  const controlPath = svg.append("path").attr("class", "bezier-curve-control-path");
  const curvePath = svg.append("path").attr("class", "bezier-curve-path");
  const tracePath = svg.append("path").attr("class", "bezier-curve-trace");
  const constructionGroup = svg.append("g").attr("class", "bezier-curve-construction");
  const currentPoint = svg.append("circle").attr("class", "bezier-curve-current").attr("r", 5);
  const pointGroup = svg.append("g").attr("class", "bezier-curve-points");

  let intervalId = null;
  let lastSync = 0;

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

  function points() {
    return (model.get("points") || []).map(coercePoint);
  }

  function xScale(value) {
    const [min, max] = bounds().x;
    return MARGIN + ((value - min) / (max - min)) * (width() - MARGIN * 2);
  }

  function yScale(value) {
    const [min, max] = bounds().y;
    return MARGIN + ((max - value) / (max - min)) * (height() - MARGIN * 2);
  }

  function xInvert(px) {
    const [min, max] = bounds().x;
    const clamped = Math.max(MARGIN, Math.min(width() - MARGIN, px));
    return min + ((clamped - MARGIN) / (width() - MARGIN * 2)) * (max - min);
  }

  function yInvert(py) {
    const [min, max] = bounds().y;
    const clamped = Math.max(MARGIN, Math.min(height() - MARGIN, py));
    return max - ((clamped - MARGIN) / (height() - MARGIN * 2)) * (max - min);
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
    playButton.innerHTML = model.get("playing") ? PAUSE_ICON : PLAY_ICON;
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
          renderFrame();
        })
        .on("end", function () {
          select(this).classed("is-dragging", false);
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
    if (model.get("playing")) {
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
    model.save_changes();
    renderFrame();
  });

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
      renderFrame();
    });
  });

  renderFrame();
  syncCurrent(true);
  if (model.get("playing")) startPlaying();

  return () => {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };
}

export default { render };
