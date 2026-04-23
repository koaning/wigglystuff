import * as d3 from "../d3.min.js";

const STYLE = `
.wiggly-treemap {
  --bg: #ffffff;
  --fg: #1f2328;
  --muted: #6b7280;
  color-scheme: light dark;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--fg);
  width: 100%;
}
:host([data-theme="dark"]) .wiggly-treemap,
.dark .wiggly-treemap,
.dark-theme .wiggly-treemap {
  --bg: #1a1a1a;
  --fg: #e6e6e6;
  --muted: #a0a0a0;
}
.wiggly-treemap-breadcrumbs {
  width: 100%;
  padding: 0.3rem 0.4rem;
  background: transparent;
  font: inherit;
  text-align: left;
  border: none;
  cursor: pointer;
  color: var(--fg);
}
.wiggly-treemap-breadcrumbs:disabled { cursor: default; color: var(--muted); }
.wiggly-treemap-chart {
  position: relative;
  overflow: hidden;
  margin: 0 0 4px 0;
  background: var(--bg);
}
.wiggly-treemap-node {
  position: absolute;
  box-sizing: border-box;
  overflow: hidden;
  padding: 2px 5px;
  border: 1px solid rgba(0, 0, 0, 0.25);
  font-size: 11px;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
  transition: left 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              top 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              width 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              height 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              background-color 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              color 0.6s cubic-bezier(0.33, 1, 0.68, 1),
              opacity 0.4s ease-out;
}
.wiggly-treemap-node.-clickable { cursor: pointer; }
.wiggly-treemap-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
`;

const NEUTRAL_COLOR = "#6b7280";

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

function pathKey(node) {
  return nodePath(node).join("\u0000");
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

function positionElement(elem, node, extent, width, height) {
  const left = ((node.x0 - extent.sx0) / extent.sdx) * width;
  const top = ((node.y0 - extent.sy0) / extent.sdy) * height;
  const w = ((node.x1 - node.x0) / extent.sdx) * width;
  const h = ((node.y1 - node.y0) / extent.sdy) * height;
  elem.style.left = left + "px";
  elem.style.top = top + "px";
  elem.style.width = Math.max(w, 0) + "px";
  elem.style.height = Math.max(h, 0) + "px";
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
  const tops = hierarchy.children || [];
  tops.forEach((top, i) => {
    const color = palette[i % palette.length];
    top.each((desc) => {
      desc._color = color;
    });
  });
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
  root.appendChild(chart);
  el.appendChild(root);

  const nodeElements = new Map(); // pathKey -> { elem, node }
  let hierarchy = null;
  let selected = null;
  let lastExtent = null;
  let lastMeasuredWidth = null;

  function measuredWidth() {
    const raw = model.get("width");
    return typeof raw === "number" ? raw : chart.clientWidth || 600;
  }

  function paletteFromModel() {
    const p = model.get("palette");
    return p && p.length ? p : [NEUTRAL_COLOR];
  }

  function applyTreemap(width, height) {
    d3.treemap()
      .size([width, height])
      .paddingTop(18)
      .paddingInner(1)
      .paddingOuter(2)(hierarchy);
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

    if (!data || !data.name) {
      chart.innerHTML = "";
      nodeElements.clear();
      hierarchy = null;
      selected = null;
      lastExtent = null;
      breadcrumbsBtn.textContent = "";
      breadcrumbsBtn.disabled = true;
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

    chart.innerHTML = "";
    nodeElements.clear();
    lastExtent = null;
    layout();
  }

  function layout() {
    if (!hierarchy || !selected) return;

    const width = measuredWidth();
    const height = model.get("height") || 400;
    const valueCol = model.get("value_col") || "";
    const maxDepth = model.get("max_depth") || 3;

    const visible = visibleDescendants(selected, maxDepth);
    const visibleKeys = new Set();
    for (const node of visible) visibleKeys.add(pathKey(node));

    const newExtent = extentOf(selected);
    const oldExtent = lastExtent || newExtent;

    let createdAny = false;
    for (const node of visible) {
      const key = pathKey(node);
      const existing = nodeElements.get(key);
      if (existing) {
        existing.node = node;
        continue;
      }
      const elem = document.createElement("div");
      elem.className = "wiggly-treemap-node";
      const label = document.createElement("div");
      label.className = "wiggly-treemap-label";
      elem.appendChild(label);
      elem.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const entry = nodeElements.get(key);
        if (entry) onNodeClick(entry.node);
      });
      chart.appendChild(elem);
      positionElement(elem, node, oldExtent, width, height);
      elem.style.opacity = "0";
      nodeElements.set(key, { elem, node });
      createdAny = true;
    }

    if (createdAny) void chart.offsetHeight;

    for (const [key, entry] of nodeElements) {
      const { elem, node } = entry;
      positionElement(elem, node, newExtent, width, height);

      if (visibleKeys.has(key)) {
        const isLeaf = !node.children;
        elem.classList.toggle("-clickable", !isLeaf);
        const bg = node._color || NEUTRAL_COLOR;
        elem.style.backgroundColor = bg;
        elem.style.color = "#ffffff";
        const nameText = node.data.name;
        const valueText = labelFor(node, valueCol);
        const labelText = valueText ? `${nameText} — ${valueText}` : nameText;
        elem.firstChild.textContent = labelText;
        elem.title = labelText;
        elem.style.opacity = "1";
      } else {
        elem.style.opacity = "0";
        const staleEl = elem;
        const staleKey = key;
        setTimeout(() => {
          if (staleEl.style.opacity !== "0") return;
          if (staleEl.parentNode === chart) chart.removeChild(staleEl);
          const curr = nodeElements.get(staleKey);
          if (curr && curr.elem === staleEl) nodeElements.delete(staleKey);
        }, 650);
      }
    }

    lastExtent = newExtent;
    updateBreadcrumbs();
  }

  function updateBreadcrumbs() {
    if (!selected) {
      breadcrumbsBtn.textContent = "";
      breadcrumbsBtn.disabled = true;
      return;
    }
    const path = nodePath(selected);
    const display =
      selected.data.display || defaultFormat(selected.value || 0);
    const nLeaves = selected.leaves ? selected.leaves().length : 0;
    const leafWord = nLeaves === 1 ? "leaf" : "leaves";
    const suffix = display
      ? `— ${display} (${nLeaves} ${leafWord})`
      : `(${nLeaves} ${leafWord})`;
    breadcrumbsBtn.textContent = `${path.join(" / ")} ${suffix}`;
    breadcrumbsBtn.disabled = !selected.parent;
  }

  function setSelected(node) {
    selected = node;
    model.set("selected_path", nodePath(node));
    model.save_changes();
    layout();
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
    lastExtent = null;
    layout();
  });
  resizeObserver.observe(chart);

  model.on("change:data", build);
  model.on("change:width", build);
  model.on("change:height", build);
  model.on("change:value_col", build);
  model.on("change:palette", () => {
    if (!hierarchy) return;
    assignColors(hierarchy, paletteFromModel());
    layout();
  });
  model.on("change:max_depth", layout);
  model.on("change:selected_path", () => {
    if (!hierarchy) return;
    const synced = model.get("selected_path") || [];
    const target = synced.length ? findNodeByPath(hierarchy, synced) : hierarchy;
    if (target && target !== selected) {
      selected = target;
      layout();
    }
  });

  build();
}

export default { render };
