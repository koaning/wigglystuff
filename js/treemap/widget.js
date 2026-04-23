import * as d3 from "../d3.min.js";

const STYLE = `
.wiggly-treemap {
  --bg: #ffffff;
  --fg: #1f2328;
  --path-current: #101828;
  --muted: #667085;
  --tile-stroke: rgba(255, 255, 255, 0.9);
  --hover-stroke: rgba(17, 24, 39, 0.48);
  color-scheme: light dark;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--fg);
  width: 100%;
}
:host([data-theme="dark"]) .wiggly-treemap,
.dark .wiggly-treemap,
.dark-theme .wiggly-treemap,
[data-theme="dark"] .wiggly-treemap {
  --bg: #111316;
  --fg: #f2f4f7;
  --path-current: #ffffff;
  --muted: #a3aab7;
  --tile-stroke: rgba(17, 19, 22, 0.92);
  --hover-stroke: rgba(255, 255, 255, 0.56);
}
.wiggly-treemap-topbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) max-content;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 2rem;
  padding: 0.35rem 0.45rem;
  font: inherit;
  font-size: 0.9rem;
  text-align: left;
  color: var(--fg);
}
.wiggly-treemap-path,
.wiggly-treemap-meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.wiggly-treemap-path {
  display: flex;
  align-items: center;
  min-width: 0;
}
.wiggly-treemap-path-part {
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 0 1 auto;
}
.wiggly-treemap-path-part.-last {
  flex: 0 0 auto;
  max-width: min(70%, 32rem);
}
.wiggly-treemap-path-separator {
  flex: 0 0 auto;
}
.wiggly-treemap-path-part.-clickable {
  cursor: pointer;
}
.wiggly-treemap-path-part.-clickable:hover {
  text-decoration: underline;
  text-underline-offset: 0.18rem;
}
.wiggly-treemap-current-path {
  color: var(--path-current);
  font-weight: 600;
}
.wiggly-treemap-next-path {
  color: var(--muted);
}
.wiggly-treemap-meta {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
.wiggly-treemap-chart {
  position: relative;
  overflow: hidden;
  margin: 0 0 4px 0;
  background: var(--bg);
  border-radius: 8px;
  contain: layout paint style;
}
.wiggly-treemap-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
`;

const DEFAULT_PALETTE = [
  "#1d4ed8",
  "#0f766e",
  "#b45309",
  "#b91c1c",
  "#6d28d9",
  "#15803d",
  "#be185d",
  "#475569",
];
const NEUTRAL_COLOR = "#6b7280";
const TILE_TEXT_COLOR = "#ffffff";
const ANIMATION_MS = 420;
const MAX_LABELS = 450;
const MIN_RECT_SIDE = 0.55;
const MIN_HIT_AREA = 12;

function defaultFormat(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  if (Number.isInteger(v)) return String(v);
  return (Math.round(v * 100) / 100).toFixed(2);
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "";
  if (value > 0 && value < 0.1) return "<0.1%";
  if (value >= 99.95 && value < 100) return "99.9%";
  return `${value.toFixed(1)}%`;
}

function pickValue(rawValue, valueCol) {
  if (rawValue === null || rawValue === undefined) return 0;
  if (typeof rawValue === "number") return rawValue;
  if (typeof rawValue === "object" && valueCol) {
    const v = rawValue[valueCol];
    return typeof v === "number" ? v : 0;
  }
  return 0;
}

function labelFor(node, valueCol) {
  const display = node.data.display;
  if (typeof display === "string") return display;
  return defaultFormat(pickValue(node.data.value, valueCol));
}

function nodePath(node) {
  const parts = [];
  let cur = node;
  while (cur) {
    parts.unshift(cur.data.name);
    cur = cur.parent;
  }
  return parts;
}

function topLevelName(node) {
  let cur = node;
  while (cur.parent && cur.parent.parent) cur = cur.parent;
  return cur.data.name;
}

function isSamePath(a, b) {
  if (a.length !== b.length) return false;
  return a.every((part, index) => part === b[index]);
}

function findNodeByPath(root, path) {
  if (!path || path.length === 0) return root;
  let cur = root;
  if (cur.data.name !== path[0]) return null;
  for (let i = 1; i < path.length; i++) {
    if (!cur.children) return null;
    const next = cur.children.find((c) => c.data.name === path[i]);
    if (!next) return null;
    cur = next;
  }
  return cur;
}

function extentOf(node) {
  return {
    sx0: node.x0,
    sy0: node.y0,
    sdx: node.x1 - node.x0 || 1,
    sdy: node.y1 - node.y0 || 1,
  };
}

function interpolateExtent(a, b, t) {
  return {
    sx0: a.sx0 + (b.sx0 - a.sx0) * t,
    sy0: a.sy0 + (b.sy0 - a.sy0) * t,
    sdx: a.sdx + (b.sdx - a.sdx) * t,
    sdy: a.sdy + (b.sdy - a.sdy) * t,
  };
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function visibleDescendants(selected, maxDepth) {
  if (!selected.children || selected.children.length === 0) return [selected];
  const out = [];
  function walk(node, rel) {
    if (rel > maxDepth) return;
    out.push(node);
    if (node.children) for (const c of node.children) walk(c, rel + 1);
  }
  if (selected.children) {
    for (const c of selected.children) walk(c, 1);
  }
  return out;
}

function assignSiblingIndexes(hierarchy) {
  hierarchy.each((node) => {
    if (!node.children) return;
    node.children.forEach((child, index) => {
      child._siblingIndex = index;
    });
  });
}

function anchorForView(node, viewRoot) {
  if (!node || !viewRoot || node === viewRoot) return null;
  let cur = node;
  while (cur.parent && cur.parent !== viewRoot) cur = cur.parent;
  return cur.parent === viewRoot ? cur : null;
}

function paletteColor(index) {
  const safeIndex = Math.max(0, index || 0);
  const cycle = Math.floor(safeIndex / DEFAULT_PALETTE.length);
  const base = DEFAULT_PALETTE[safeIndex % DEFAULT_PALETTE.length] || NEUTRAL_COLOR;
  const color = d3.color(base) || d3.color(NEUTRAL_COLOR);
  return color.brighter(cycle * 0.18).formatHex();
}

function colorForNodeInView(node, viewRoot) {
  if (!node || !viewRoot) return NEUTRAL_COLOR;
  if (node === viewRoot && (!viewRoot.children || viewRoot.children.length === 0)) {
    return DEFAULT_PALETTE[0];
  }

  const anchor = anchorForView(node, viewRoot);
  if (!anchor) return NEUTRAL_COLOR;

  const anchorIndex = anchor._siblingIndex || 0;
  const base = d3.color(paletteColor(anchorIndex)) || d3.color(DEFAULT_PALETTE[0]);
  const relativeDepth = Math.max(0, node.depth - anchor.depth);
  const siblingShift = ((node._siblingIndex || 0) % 5) * 0.025;
  return base.brighter(Math.min(0.32, relativeDepth * 0.11 + siblingShift)).formatHex();
}

function isDescendantOrSelf(node, ancestor) {
  let cur = node;
  while (cur) {
    if (cur === ancestor) return true;
    cur = cur.parent;
  }
  return false;
}

function projectedBox(node, extent, width, height) {
  const left = ((node.x0 - extent.sx0) / extent.sdx) * width;
  const top = ((node.y0 - extent.sy0) / extent.sdy) * height;
  const w = ((node.x1 - node.x0) / extent.sdx) * width;
  const h = ((node.y1 - node.y0) / extent.sdy) * height;
  return { left, top, width: Math.max(w, 0), height: Math.max(h, 0) };
}

function roundedRect(ctx, x, y, width, height, radius) {
  const r = Math.max(0, Math.min(radius, width / 2, height / 2));
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, r);
    return;
  }
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + width, y, x + width, y + height, r);
  ctx.arcTo(x + width, y + height, x, y + height, r);
  ctx.arcTo(x, y + height, x, y, r);
  ctx.arcTo(x, y, x + width, y, r);
}

function fitText(ctx, text, maxWidth) {
  if (!text || maxWidth <= 0) return "";
  if (ctx.measureText(text).width <= maxWidth) return text;
  const ellipsis = "...";
  let lo = 0;
  let hi = text.length;
  while (lo < hi) {
    const mid = Math.ceil((lo + hi) / 2);
    if (ctx.measureText(text.slice(0, mid) + ellipsis).width <= maxWidth) {
      lo = mid;
    } else {
      hi = mid - 1;
    }
  }
  return lo > 0 ? text.slice(0, lo) + ellipsis : "";
}

function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "wiggly-treemap";
  const style = document.createElement("style");
  style.textContent = STYLE;
  root.appendChild(style);

  const topbar = document.createElement("div");
  topbar.className = "wiggly-treemap-topbar";
  const pathEl = document.createElement("span");
  pathEl.className = "wiggly-treemap-path";
  const metaEl = document.createElement("span");
  metaEl.className = "wiggly-treemap-meta";
  topbar.append(pathEl, metaEl);
  root.appendChild(topbar);

  const chart = document.createElement("div");
  chart.className = "wiggly-treemap-chart";
  const canvas = document.createElement("canvas");
  canvas.className = "wiggly-treemap-canvas";
  chart.appendChild(canvas);
  root.appendChild(chart);
  el.appendChild(root);

  const ctx = canvas.getContext("2d");
  let hierarchy = null;
  let selected = null;
  let currentExtent = null;
  let targetExtent = null;
  let animationFrame = null;
  let lastMeasuredWidth = null;
  let hitNodes = [];
  let hoveredNode = null;
  let hoverTarget = null;
  let cachedVisible = null;
  let cachedSelected = null;
  let cachedMaxDepth = null;
  let colorTransition = null;

  function measuredWidth() {
    const raw = model.get("width");
    return typeof raw === "number" ? raw : chart.clientWidth || 600;
  }

  function currentColors() {
    const computed = getComputedStyle(root);
    return {
      bg: computed.getPropertyValue("--bg").trim() || "#ffffff",
      stroke: computed.getPropertyValue("--tile-stroke").trim() || "rgba(255,255,255,0.9)",
      hoverStroke: computed.getPropertyValue("--hover-stroke").trim() || "rgba(255,255,255,0.98)",
      muted: computed.getPropertyValue("--muted").trim() || "#667085",
    };
  }

  function syncCanvasSize(width, height) {
    const dpr = window.devicePixelRatio || 1;
    const pixelWidth = Math.max(1, Math.round(width * dpr));
    const pixelHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function applyTreemap(width, height) {
    d3.treemap()
      .size([width, height])
      .paddingTop((node) => (node.children ? 20 : 0))
      .paddingInner(1)
      .paddingOuter(2)
      .round(true)(hierarchy);
  }

  function invalidateVisibleCache() {
    cachedVisible = null;
    cachedSelected = null;
    cachedMaxDepth = null;
  }

  function getVisibleNodes(maxDepth) {
    if (
      cachedVisible &&
      cachedSelected === selected &&
      cachedMaxDepth === maxDepth
    ) {
      return cachedVisible;
    }
    cachedVisible = visibleDescendants(selected, maxDepth);
    cachedSelected = selected;
    cachedMaxDepth = maxDepth;
    return cachedVisible;
  }

  function colorForDraw(node) {
    if (!colorTransition) return colorForNodeInView(node, selected);

    const to = colorForNodeInView(node, colorTransition.toView);
    const from = isDescendantOrSelf(node, colorTransition.fromView)
      ? colorForNodeInView(node, colorTransition.fromView)
      : to;
    return d3.interpolateRgb(from, to)(colorTransition.progress);
  }

  function build() {
    const data = model.get("data");
    const widthRaw = model.get("width");
    const height = model.get("height") || 400;
    const valueCol = model.get("value_col") || "";
    chart.style.width =
      typeof widthRaw === "number" ? widthRaw + "px" : widthRaw || "600px";
    chart.style.height = height + "px";
    const width = measuredWidth();
    syncCanvasSize(width, height);

    if (!data || !data.name) {
      hierarchy = null;
      selected = null;
      currentExtent = null;
      targetExtent = null;
      hitNodes = [];
      hoverTarget = null;
      invalidateVisibleCache();
      pathEl.textContent = "";
      metaEl.textContent = "";
      ctx.clearRect(0, 0, width, height);
      return;
    }

    hierarchy = d3
      .hierarchy(data)
      .sum((d) =>
        d.children && d.children.length ? 0 : pickValue(d.value, valueCol)
      )
      .sort((a, b) => b.value - a.value);

    applyTreemap(width, height);
    assignSiblingIndexes(hierarchy);
    lastMeasuredWidth = width;

    const syncedPath = model.get("selected_path") || [];
    const byPath = syncedPath.length
      ? findNodeByPath(hierarchy, syncedPath)
      : null;
    selected = byPath || hierarchy;
    currentExtent = extentOf(selected);
    targetExtent = currentExtent;
    colorTransition = null;
    invalidateVisibleCache();
    updateBreadcrumbs();
    draw(currentExtent);
  }

  function draw(extent) {
    if (!hierarchy || !selected) return;
    const width = measuredWidth();
    const height = model.get("height") || 400;
    const valueCol = model.get("value_col") || "";
    const maxDepth = model.get("max_depth") || 3;
    const colors = currentColors();
    syncCanvasSize(width, height);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, width, height);

    const visible = getVisibleNodes(maxDepth);
    const drawItems = [];
    hitNodes = [];

    for (const node of visible) {
      const box = projectedBox(node, extent, width, height);
      if (box.width < MIN_RECT_SIDE || box.height < MIN_RECT_SIDE) continue;
      drawItems.push({ node, box });
      if (box.width * box.height >= MIN_HIT_AREA) hitNodes.push({ node, box });
    }

    let labelsDrawn = 0;
    for (const { node, box } of drawItems) {
      const fill = colorForDraw(node);
      const radius = Math.min(7, Math.max(2, Math.min(box.width, box.height) / 8));
      ctx.save();
      roundedRect(ctx, box.left, box.top, box.width, box.height, radius);
      ctx.fillStyle = fill;
      ctx.fill();
      if (box.width > 3 && box.height > 3) {
        ctx.lineWidth = 1;
        ctx.strokeStyle = colors.stroke;
        ctx.stroke();
      }
      ctx.restore();

      if (labelsDrawn >= MAX_LABELS) continue;
      const nameText = node.data.name;
      const valueText = labelFor(node, valueCol);
      const canShowName = box.width >= 46 && box.height >= 18;
      const canShowValue = box.width >= 68 && box.height >= 34 && valueText;
      if (!canShowName) continue;

      ctx.save();
      ctx.beginPath();
      ctx.rect(box.left + 2, box.top + 2, Math.max(0, box.width - 4), Math.max(0, box.height - 4));
      ctx.clip();
      ctx.fillStyle = TILE_TEXT_COLOR;
      ctx.font = "600 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.textBaseline = "top";
      const label = fitText(ctx, nameText, box.width - 12);
      if (label) {
        ctx.fillText(label, box.left + 6, box.top + 5);
        labelsDrawn += 1;
      }
      if (canShowValue) {
        ctx.globalAlpha = 0.78;
        ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
        const value = fitText(ctx, valueText, box.width - 12);
        if (value) ctx.fillText(value, box.left + 6, box.top + 20);
      }
      ctx.restore();
    }

    if (drawItems.length === 0 && selected.children && selected.children.length) {
      ctx.fillStyle = colors.muted;
      ctx.font = "13px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.fillText("Zoom in or increase the widget size to see these tiny items.", 12, 18);
    }

    if (hoverTarget && hoverTarget !== selected) {
      const box = projectedBox(hoverTarget, extent, width, height);
      if (box.width >= 2 && box.height >= 2) {
        ctx.save();
        roundedRect(
          ctx,
          box.left,
          box.top,
          box.width,
          box.height,
          Math.min(8, Math.max(2, Math.min(box.width, box.height) / 8))
        );
        ctx.lineWidth = Math.min(2.75, Math.max(1.75, Math.min(box.width, box.height) / 26));
        ctx.strokeStyle = colors.hoverStroke;
        ctx.stroke();
        ctx.restore();
      }
    }
  }

  function animateTo(nextExtent) {
    if (animationFrame !== null) cancelAnimationFrame(animationFrame);
    const startExtent = currentExtent || nextExtent;
    const start = performance.now();
    targetExtent = nextExtent;

    function tick(now) {
      const t = Math.min(1, (now - start) / ANIMATION_MS);
      const easedT = easeOutCubic(t);
      if (colorTransition) colorTransition.progress = easedT;
      currentExtent = interpolateExtent(startExtent, targetExtent, easedT);
      draw(currentExtent);
      if (t < 1) {
        animationFrame = requestAnimationFrame(tick);
      } else {
        currentExtent = targetExtent;
        animationFrame = null;
        colorTransition = null;
        draw(currentExtent);
      }
    }
    animationFrame = requestAnimationFrame(tick);
  }

  function updateBreadcrumbs() {
    if (!selected) {
      pathEl.textContent = "";
      metaEl.textContent = "";
      return;
    }
    updateTopBar(selected);
  }

  function nodeSummary(node) {
    const valueCol = model.get("value_col") || "";
    const valueText = labelFor(node, valueCol) || defaultFormat(node.value || 0);
    const total = hierarchy && hierarchy.value ? hierarchy.value : 0;
    const percentText = total ? formatPercent((node.value / total) * 100) : "";
    const nLeaves = node.leaves ? node.leaves().length : 0;
    const leafWord = nLeaves === 1 ? "leaf" : "leaves";
    const valueSummary = percentText ? `${valueText} (${percentText})` : valueText;
    return valueSummary
      ? `${valueSummary} - ${nLeaves} ${leafWord}`
      : `${nLeaves} ${leafWord}`;
  }

  function updateTopBar(node) {
    if (!node) return;
    const path = nodePath(node);
    const selectedPath = selected ? nodePath(selected) : [];
    const commonLength = path.reduce((count, part, index) => {
      return count === index && selectedPath[index] === part ? count + 1 : count;
    }, 0);
    const currentPath = path.slice(0, commonLength).join(" / ");
    const displayPath = path.join(" / ");

    pathEl.replaceChildren();
    path.forEach((part, index) => {
      if (index > 0) {
        const separator = document.createElement("span");
        separator.textContent = " / ";
        separator.className =
          index <= commonLength
            ? "wiggly-treemap-path-separator wiggly-treemap-current-path"
            : "wiggly-treemap-path-separator wiggly-treemap-next-path";
        pathEl.appendChild(separator);
      }

      const partPath = path.slice(0, index + 1);
      const target = findNodeByPath(hierarchy, partPath);
      const isCurrent = index < commonLength;
      const partEl = document.createElement("button");
      partEl.type = "button";
      partEl.className = `wiggly-treemap-path-part ${
        isCurrent ? "wiggly-treemap-current-path" : "wiggly-treemap-next-path"
      }`;
      if (index === path.length - 1) partEl.classList.add("-last");
      partEl.textContent = part;
      if (target && !isSamePath(partPath, selectedPath)) {
        partEl.classList.add("-clickable");
        partEl.addEventListener("click", (event) => {
          event.stopPropagation();
          setSelected(target);
        });
      }
      pathEl.appendChild(partEl);
    });
    if (!path.length) {
      pathEl.textContent = currentPath || displayPath;
    }
    pathEl.title = displayPath;
    metaEl.textContent = nodeSummary(node);
    metaEl.title = `${topLevelName(node)} - ${displayPath}`;
  }

  function zoomTargetFor(node) {
    if (!node) return null;
    if (node === selected) return selected;
    let target = node;
    while (target.parent && target.parent !== selected) {
      target = target.parent;
    }
    return target;
  }

  function setSelected(node, animate = true, sync = true) {
    const previousSelected = selected;
    selected = node;
    const nextExtent = extentOf(node);
    invalidateVisibleCache();
    if (sync) {
      model.set("selected_path", nodePath(node));
      model.save_changes();
    }
    updateBreadcrumbs();
    if (animate && previousSelected && previousSelected !== node) {
      colorTransition = {
        fromView: previousSelected,
        toView: node,
        progress: 0,
      };
      animateTo(nextExtent);
    } else if (animate) {
      colorTransition = null;
      animateTo(nextExtent);
    } else {
      colorTransition = null;
      currentExtent = nextExtent;
      targetExtent = nextExtent;
      draw(currentExtent);
    }
  }

  function hitTest(x, y) {
    for (let i = hitNodes.length - 1; i >= 0; i--) {
      const { node, box } = hitNodes[i];
      if (
        x >= box.left &&
        x <= box.left + box.width &&
        y >= box.top &&
        y <= box.top + box.height
      ) {
        return node;
      }
    }
    return null;
  }

  function eventPoint(ev) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: ev.clientX - rect.left,
      y: ev.clientY - rect.top,
    };
  }

  function onNodeClick(node) {
    model.set("clicked_path", nodePath(node));
    model.save_changes();
    const target = zoomTargetFor(node);
    if (target && target !== selected) setSelected(target);
  }

  canvas.addEventListener("mousemove", (ev) => {
    if (!selected) return;
    const point = eventPoint(ev);
    const node = hitTest(point.x, point.y);
    const nextHoverTarget = zoomTargetFor(node);
    const hoverChanged = nextHoverTarget !== hoverTarget;
    const prevHoveredNode = hoveredNode;
    hoveredNode = node;
    hoverTarget = nextHoverTarget;
    chart.style.cursor = hoverTarget && hoverTarget !== selected ? "pointer" : "default";
    updateTopBar(hoverTarget || selected);
    if (node !== prevHoveredNode) {
      model.set("hovered_path", node ? nodePath(node) : []);
      model.save_changes();
    }
    if (hoverChanged) draw(currentExtent || extentOf(selected));
  });

  canvas.addEventListener("mouseleave", () => {
    const hadHover = hoveredNode !== null;
    hoveredNode = null;
    hoverTarget = null;
    chart.style.cursor = "default";
    updateTopBar(selected);
    if (hadHover) {
      model.set("hovered_path", []);
      model.save_changes();
    }
    draw(currentExtent || extentOf(selected));
  });

  canvas.addEventListener("click", (ev) => {
    const point = eventPoint(ev);
    const node = hitTest(point.x, point.y) || hoveredNode;
    if (node) onNodeClick(node);
  });

  const resizeObserver = new ResizeObserver(() => {
    if (typeof model.get("width") !== "string") return;
    if (!hierarchy) return;
    const w = measuredWidth();
    if (w === lastMeasuredWidth) return;
    lastMeasuredWidth = w;
    const height = model.get("height") || 400;
    applyTreemap(w, height);
    currentExtent = extentOf(selected);
    targetExtent = currentExtent;
    colorTransition = null;
    invalidateVisibleCache();
    draw(currentExtent);
  });
  resizeObserver.observe(chart);

  model.on("change:data", build);
  model.on("change:width", build);
  model.on("change:height", build);
  model.on("change:value_col", build);
  model.on("change:max_depth", () => {
    invalidateVisibleCache();
    draw(currentExtent || extentOf(selected));
  });
  model.on("change:selected_path", () => {
    if (!hierarchy) return;
    const synced = model.get("selected_path") || [];
    const target = synced.length ? findNodeByPath(hierarchy, synced) : hierarchy;
    if (target && target !== selected) {
      setSelected(target, true, false);
    }
  });

  build();
}

export default { render };
