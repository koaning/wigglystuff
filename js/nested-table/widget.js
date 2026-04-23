const STYLE = `
.wiggly-nested-table {
  --bg: transparent;
  --fg: #1f2328;
  --muted: #6b7280;
  --row-border: #e5e7eb;
  --hover: rgba(15, 23, 42, 0.04);
  --header-bg: rgba(15, 23, 42, 0.025);
  --selected-bg: rgba(59, 130, 246, 0.1);
  --selected-accent: #3b82f6;
  color-scheme: light dark;
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", sans-serif;
  font-size: 13px;
}
:host([data-theme="dark"]) .wiggly-nested-table,
.dark .wiggly-nested-table,
.dark-theme .wiggly-nested-table {
  --fg: #e6e6e6;
  --muted: #9ca3af;
  --row-border: #2a2d33;
  --hover: rgba(255, 255, 255, 0.05);
  --header-bg: rgba(255, 255, 255, 0.03);
  --selected-bg: rgba(96, 165, 250, 0.18);
  --selected-accent: #60a5fa;
}
.wiggly-nested-table table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg);
  font-variant-numeric: tabular-nums;
}
.wiggly-nested-table thead th {
  text-align: left;
  font-weight: 500;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--row-border);
  background-color: var(--header-bg);
  position: sticky;
  top: 0;
}
.wiggly-nested-table thead th.num { text-align: right; }
.wiggly-nested-table tbody td {
  padding: 0.35rem 0.75rem;
  vertical-align: middle;
  border-bottom: 1px solid var(--row-border);
  transition: background-color 0.15s ease-out;
}
.wiggly-nested-table tbody tr:last-child td { border-bottom: none; }
.wiggly-nested-table tbody tr:hover td { background-color: var(--hover); }
.wiggly-nested-table tbody tr.-selected td { background-color: var(--selected-bg); }
.wiggly-nested-table tbody tr.-selected td:first-child {
  box-shadow: inset 2px 0 0 var(--selected-accent);
}
.wiggly-nested-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.wiggly-nested-table td.pct { color: var(--muted); text-align: right; font-size: 12px; }
.wiggly-nested-table td.name-cell.-clickable { cursor: pointer; }
.wiggly-nested-table .row-name {
  user-select: none;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.wiggly-nested-table .chev {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  color: var(--muted);
  flex-shrink: 0;
}
.wiggly-nested-table .chev.-empty { visibility: hidden; }
.wiggly-nested-table .chev svg {
  transition: transform 0.15s ease-out;
}
.wiggly-nested-table .chev.-open svg { transform: rotate(90deg); }
.wiggly-nested-table .name-label { font-weight: 500; }
`;

const CHEV_SVG = `<svg width="10" height="10" viewBox="0 0 10 10"><path d="M3.5 2 L6.5 5 L3.5 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

function defaultFormat(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return "";
  if (Number.isInteger(v)) return String(v);
  return (Math.round(v * 100) / 100).toFixed(2);
}

function pickValue(rawValue, col) {
  if (rawValue === null || rawValue === undefined) return null;
  if (typeof rawValue === "number") {
    return col === "value" || !col ? rawValue : null;
  }
  if (typeof rawValue === "object") {
    const v = rawValue[col];
    return typeof v === "number" ? v : null;
  }
  return null;
}

function labelFor(node, col) {
  const display = node.display;
  if (display && typeof display === "object" && display[col] !== undefined) {
    return display[col];
  }
  const v = pickValue(node.value, col);
  return defaultFormat(v);
}

function columnHeader(col) {
  if (col === "value") return "Value";
  return col;
}

function pathToKey(path) {
  return path.join("\u0000");
}

function render({ model, el }) {
  const root = document.createElement("div");
  root.className = "wiggly-nested-table";
  const style = document.createElement("style");
  style.textContent = STYLE;
  root.appendChild(style);

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");
  table.appendChild(thead);
  table.appendChild(tbody);
  root.appendChild(table);
  el.appendChild(root);

  let expanded = new Set();
  const rowByKey = new Map(); // pathKey -> <tr>
  let selectedKey = null;

  function effectiveColumns() {
    const cols = model.get("columns") || [];
    return cols.length ? cols : ["value"];
  }

  function seedExpanded() {
    const data = model.get("data");
    const depth = model.get("initial_expand_depth") || 0;
    const synced = model.get("expanded_paths") || [];
    if (synced.length) {
      expanded = new Set(synced.map((p) => pathToKey(p)));
      return;
    }
    expanded = new Set();
    function walk(node, path, d) {
      if (d >= depth || !node.children) return;
      const here = path.concat(node.name);
      expanded.add(pathToKey(here));
      for (const child of node.children) walk(child, here, d + 1);
    }
    if (data && data.name) walk(data, [], 0);
  }

  function syncExpanded() {
    const arr = [];
    for (const k of expanded) arr.push(k.split("\u0000"));
    model.set("expanded_paths", arr);
    model.save_changes();
  }

  function setSelectedKey(key) {
    if (selectedKey === key) return;
    if (selectedKey) {
      const prev = rowByKey.get(selectedKey);
      if (prev) prev.classList.remove("-selected");
    }
    selectedKey = key;
    if (key) {
      const cur = rowByKey.get(key);
      if (cur) cur.classList.add("-selected");
    }
  }

  function build() {
    root.style.width = model.get("width") || "100%";
    seedExpanded();
    const synced = model.get("selected_path") || [];
    selectedKey = synced.length ? pathToKey(synced) : null;
    redraw();
  }

  function redraw() {
    const data = model.get("data");
    const cols = effectiveColumns();
    const pctCols = new Set(model.get("show_percent") || []);

    thead.innerHTML = "";
    tbody.innerHTML = "";
    rowByKey.clear();
    if (!data || !data.name) return;

    const headerTr = document.createElement("tr");
    const nameTh = document.createElement("th");
    nameTh.textContent = "Name";
    headerTr.appendChild(nameTh);
    for (const col of cols) {
      const valTh = document.createElement("th");
      valTh.className = "num";
      valTh.textContent = columnHeader(col);
      headerTr.appendChild(valTh);
      if (pctCols.has(col)) {
        const pctTh = document.createElement("th");
        pctTh.className = "num";
        pctTh.textContent = "%";
        headerTr.appendChild(pctTh);
      }
    }
    thead.appendChild(headerTr);

    const rootTotals = {};
    for (const col of cols) {
      const v = pickValue(data.value, col);
      rootTotals[col] = v && v !== 0 ? v : 1;
    }
    renderRow(data, [], 0, rootTotals, cols, pctCols);
  }

  function renderRow(node, path, depth, rootTotals, cols, pctCols) {
    const here = path.concat(node.name);
    const key = pathToKey(here);
    const isExpanded = expanded.has(key);
    const hasChildren = !!(node.children && node.children.length);

    const tr = document.createElement("tr");
    if (key === selectedKey) tr.classList.add("-selected");
    rowByKey.set(key, tr);

    const nameTd = document.createElement("td");
    nameTd.className = "name-cell" + (hasChildren ? " -clickable" : "");
    nameTd.style.paddingLeft = 0.75 + depth * 1.2 + "rem";
    const nameWrap = document.createElement("div");
    nameWrap.className = "row-name";

    const chev = document.createElement("span");
    chev.className = "chev" + (hasChildren ? (isExpanded ? " -open" : "") : " -empty");
    chev.innerHTML = CHEV_SVG;
    nameWrap.appendChild(chev);

    const label = document.createElement("span");
    label.className = "name-label";
    label.textContent = node.name;
    nameWrap.appendChild(label);

    nameTd.addEventListener("click", (ev) => {
      ev.stopPropagation();
      setSelectedKey(key);
      model.set("selected_path", here);
      model.save_changes();
      if (!hasChildren) return;
      if (isExpanded) expanded.delete(key);
      else expanded.add(key);
      syncExpanded();
      redraw();
    });
    nameTd.appendChild(nameWrap);
    tr.appendChild(nameTd);

    for (const col of cols) {
      const valTd = document.createElement("td");
      valTd.className = "num";
      valTd.textContent = labelFor(node, col);
      tr.appendChild(valTd);
      if (pctCols.has(col)) {
        const pctTd = document.createElement("td");
        pctTd.className = "pct";
        const v = pickValue(node.value, col);
        if (v !== null && rootTotals[col]) {
          const pct = (v / rootTotals[col]) * 100;
          pctTd.textContent = (Math.round(pct * 10) / 10).toFixed(1) + "%";
        } else {
          pctTd.textContent = "";
        }
        tr.appendChild(pctTd);
      }
    }

    tbody.appendChild(tr);

    if (hasChildren && isExpanded) {
      for (const child of node.children) {
        renderRow(child, here, depth + 1, rootTotals, cols, pctCols);
      }
    }
  }

  model.on("change:data", build);
  model.on("change:columns", redraw);
  model.on("change:show_percent", redraw);
  model.on("change:initial_expand_depth", build);
  model.on("change:width", () => {
    root.style.width = model.get("width") || "100%";
  });
  model.on("change:expanded_paths", () => {
    const synced = model.get("expanded_paths") || [];
    const incoming = new Set(synced.map((p) => pathToKey(p)));
    if (
      incoming.size !== expanded.size ||
      [...incoming].some((k) => !expanded.has(k))
    ) {
      expanded = incoming;
      redraw();
    }
  });
  model.on("change:selected_path", () => {
    const synced = model.get("selected_path") || [];
    setSelectedKey(synced.length ? pathToKey(synced) : null);
  });

  build();
}

export default { render };
