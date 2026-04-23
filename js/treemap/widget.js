import * as d3 from "../d3.min.js";

const STYLE = `
.wiggly-treemap {
  --bg: #ffffff;
  --fg: #1f2328;
  --muted: #667085;
  --tile-stroke: rgba(255, 255, 255, 0.9);
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
  --muted: #a3aab7;
  --tile-stroke: rgba(17, 19, 22, 0.92);
}
.wiggly-treemap-breadcrumbs {
  width: 100%;
  min-height: 2rem;
  padding: 0.35rem 0.45rem;
  background: transparent;
  font: inherit;
  font-size: 0.9rem;
  text-align: left;
  border: none;
  cursor: pointer;
  color: var(--fg);
}
.wiggly-treemap-breadcrumbs:disabled {
  cursor: default;
  color: var(--muted);
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
  "#3b82f6",
  "#14b8a6",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#22c55e",
  "#ec4899",
  "#64748b",
];
const NEUTRAL_COLOR = "#6b7280";
const ANIMATION_MS = 420;
const MAX_LABELS = 450;
const MIN_RECT_SIDE = 0.55;
const MIN_HIT_AREA = 12;

function defaultFormat(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  if (Number.isInteger(v)) return String(v);
  return (Math.round(v * 100) / 100).toFixed(2);
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

function assignColors(hierarchy, palette) {
  const colors = palette && palette.length ? palette : DEFAULT_PALETTE;
  const tops = hierarchy.children || [];
  tops.forEach((top, i) => {
    const color = colors[i % colors.length] || NEUTRAL_COLOR;
    top.each((desc) => {
      desc._color = color;
    });
  });
  hierarchy.each((node) => {
    if (!node.children) return;
    node.children.forEach((child, index) => {
      child._siblingIndex = index;
    });
  });
}

function colorForNode(node) {
  const base = d3.color(node._color || NEUTRAL_COLOR) || d3.color(NEUTRAL_COLOR);
  const depthShift = Math.max(0, node.depth - 1) * 0.28;
  const siblingShift = ((node._siblingIndex || 0) % 5) * 0.035;
  return base.brighter(depthShift + siblingShift).formatHex();
}

function readableTextColor(fill) {
  const c = d3.color(fill);
  if (!c) return "#ffffff";
  const luminance = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255;
  return luminance > 0.58 ? "#111827" : "#ffffff";
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

  const breadcrumbsBtn = document.createElement("button");
  breadcrumbsBtn.className = "wiggly-treemap-breadcrumbs";
  breadcrumbsBtn.type = "button";
  root.appendChild(breadcrumbsBtn);

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
  let cachedVisible = null;
  let cachedSelected = null;
  let cachedMaxDepth = null;

  function measuredWidth() {
    const raw = model.get("width");
    return typeof raw === "number" ? raw : chart.clientWidth || 600;
  }

  function paletteFromModel() {
    const p = model.get("palette");
    return p && p.length ? p : DEFAULT_PALETTE;
  }

  function currentColors() {
    const computed = getComputedStyle(root);
    return {
      bg: computed.getPropertyValue("--bg").trim() || "#ffffff",
      stroke: computed.getPropertyValue("--tile-stroke").trim() || "rgba(255,255,255,0.9)",
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
      invalidateVisibleCache();
      breadcrumbsBtn.textContent = "";
      breadcrumbsBtn.disabled = true;
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
    assignColors(hierarchy, paletteFromModel());
    lastMeasuredWidth = width;

    const syncedPath = model.get("selected_path") || [];
    const byPath = syncedPath.length
      ? findNodeByPath(hierarchy, syncedPath)
      : null;
    selected = byPath || hierarchy;
    currentExtent = extentOf(selected);
    targetExtent = currentExtent;
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
      const fill = colorForNode(node);
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
      const textColor = readableTextColor(fill);
      ctx.fillStyle = textColor;
      ctx.font = "600 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.textBaseline = "top";
      const label = fitText(ctx, nameText, box.width - 12);
      if (label) {
        ctx.fillText(label, box.left + 6, box.top + 5);
        labelsDrawn += 1;
      }
      if (canShowValue) {
        ctx.globalAlpha = textColor === "#ffffff" ? 0.78 : 0.68;
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
  }

  function animateTo(nextExtent) {
    if (animationFrame !== null) cancelAnimationFrame(animationFrame);
    const startExtent = currentExtent || nextExtent;
    const start = performance.now();
    targetExtent = nextExtent;

    function tick(now) {
      const t = Math.min(1, (now - start) / ANIMATION_MS);
      currentExtent = interpolateExtent(startExtent, targetExtent, easeOutCubic(t));
      draw(currentExtent);
      if (t < 1) {
        animationFrame = requestAnimationFrame(tick);
      } else {
        currentExtent = targetExtent;
        animationFrame = null;
        draw(currentExtent);
      }
    }
    animationFrame = requestAnimationFrame(tick);
  }

  function updateBreadcrumbs() {
    if (!selected) {
      breadcrumbsBtn.textContent = "";
      breadcrumbsBtn.disabled = true;
      return;
    }
    const path = nodePath(selected);
    const display = selected.data.display || defaultFormat(selected.value || 0);
    const nLeaves = selected.leaves ? selected.leaves().length : 0;
    const leafWord = nLeaves === 1 ? "leaf" : "leaves";
    const suffix = display
      ? ` - ${display} (${nLeaves} ${leafWord})`
      : `(${nLeaves} ${leafWord})`;
    breadcrumbsBtn.textContent = `${path.join(" / ")} ${suffix}`;
    breadcrumbsBtn.disabled = !selected.parent;
  }

  function setSelected(node, animate = true) {
    selected = node;
    const nextExtent = extentOf(node);
    invalidateVisibleCache();
    model.set("selected_path", nodePath(node));
    model.save_changes();
    updateBreadcrumbs();
    if (animate) animateTo(nextExtent);
    else {
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
    let target = node;
    while (target.parent && target.parent !== selected) {
      target = target.parent;
    }
    if (target !== selected && target.children) setSelected(target);
  }

  canvas.addEventListener("mousemove", (ev) => {
    if (!selected) return;
    const point = eventPoint(ev);
    const node = hitTest(point.x, point.y);
    hoveredNode = node;
    chart.style.cursor = node && node.children ? "pointer" : "default";
    if (node) {
      const valueText = labelFor(node, model.get("value_col") || "");
      chart.title = valueText ? `${nodePath(node).join(" / ")} - ${valueText}` : nodePath(node).join(" / ");
    } else {
      chart.title = "";
    }
  });

  canvas.addEventListener("mouseleave", () => {
    hoveredNode = null;
    chart.style.cursor = "default";
    chart.title = "";
  });

  canvas.addEventListener("click", (ev) => {
    const point = eventPoint(ev);
    const node = hitTest(point.x, point.y) || hoveredNode;
    if (node) onNodeClick(node);
  });

  breadcrumbsBtn.addEventListener("click", () => {
    if (selected && selected.parent) setSelected(selected.parent);
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
    invalidateVisibleCache();
    draw(currentExtent);
  });
  resizeObserver.observe(chart);

  model.on("change:data", build);
  model.on("change:width", build);
  model.on("change:height", build);
  model.on("change:value_col", build);
  model.on("change:palette", () => {
    if (!hierarchy) return;
    assignColors(hierarchy, paletteFromModel());
    draw(currentExtent || extentOf(selected));
  });
  model.on("change:max_depth", () => {
    invalidateVisibleCache();
    draw(currentExtent || extentOf(selected));
  });
  model.on("change:selected_path", () => {
    if (!hierarchy) return;
    const synced = model.get("selected_path") || [];
    const target = synced.length ? findNodeByPath(hierarchy, synced) : hierarchy;
    if (target && target !== selected) {
      selected = target;
      invalidateVisibleCache();
      updateBreadcrumbs();
      animateTo(extentOf(selected));
    }
  });

  build();
}

export default { render };
