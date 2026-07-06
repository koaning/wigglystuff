function text(value) {
  return document.createTextNode(value == null ? "" : String(value));
}

function span(className, value) {
  const node = document.createElement("span");
  node.className = className;
  node.textContent = value == null ? "" : String(value);
  return node;
}

// Render a value that may carry a rich HTML representation. Falls back to the
// plain-text repr when no html is present. innerHTML does not execute <script>,
// and the widget lives in a shadow root so styles stay isolated.
function valueNode(className, reprValue, html) {
  const node = document.createElement("span");
  node.className = className;
  if (html != null && html !== "") {
    node.classList.add("liveedit-html");
    node.innerHTML = html;
  } else {
    node.textContent = reprValue == null ? "" : String(reprValue);
  }
  return node;
}

function codeLine(line) {
  const row = document.createElement("div");
  row.className = "liveedit-line";
  if (line.hover) row.dataset.hover = line.hover;
  if (line.assigns?.length) row.dataset.assigns = line.assigns.join(" ");
  if (line.returns?.length) row.dataset.return = line.returns.join(" ");
  if (line.loop_body?.length) row.dataset.loopBody = line.loop_body.join(" ");

  const tokens = [...(line.tokens || [])].sort((a, b) => a.start - b.start);
  let cursor = 0;
  for (const token of tokens) {
    if (token.start < cursor) continue;
    row.append(text(line.text.slice(cursor, token.start)));
    const tokenClass = token.type === "var" ? "liveedit-var" : `liveedit-${token.type}`;
    const tokenNode = span(tokenClass, line.text.slice(token.start, token.end));
    if (token.type === "var") tokenNode.dataset.var = token.name;
    row.append(tokenNode);
    cursor = token.end;
  }
  row.append(text(line.text.slice(cursor)));
  return row;
}

function kvRow(item) {
  const row = document.createElement("div");
  row.className = "liveedit-kv";
  row.dataset.hover = `var:${item.name}`;
  row.dataset.var = item.name;
  row.title = item.repr;
  row.append(span("liveedit-kv-name", item.name.padEnd(6, " ")));
  row.append(text(" = "));
  row.append(valueNode("liveedit-value", item.repr, item.html));
  return row;
}

function returnChip(returned, error) {
  const row = document.createElement("div");
  row.className = "liveedit-return";
  if (!returned) {
    if (error) {
      row.classList.add("liveedit-return-raised");
      row.textContent = "raised ";
      row.append(span("liveedit-return-error", error.type));
      return row;
    }
    row.textContent = "returned ";
    row.append(span("liveedit-muted", "None"));
    return row;
  }
  row.textContent = "returned ";
  const value = valueNode("liveedit-return-value", returned.repr, returned.html);
  row.append(value);
  row.title = returned.repr;
  return row;
}

const CHART_PALETTE_SIZE = 7;

function chartIcon() {
  const svg = svgEl("svg", {
    class: "liveedit-chart-icon",
    viewBox: "0 0 16 16",
    width: 12,
    height: 12,
  });
  svg.append(
    svgEl("polyline", {
      points: "1,11 5,7 8,9 15,2",
      fill: "none",
      "stroke-width": 1.6,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
    })
  );
  return svg;
}

function tableForLoop(loop, chartState, colVisible, nested) {
  const table = document.createElement("table");
  table.className = "liveedit-table";

  const numerics = loop.numerics || {};
  const cols = (loop.columns || []).filter(colVisible);
  // chartState maps a loop id to an array of panels; each panel is an array of
  // column names. A column is "active" if it appears in any panel.
  const panels = chartState.get(loop.loop_id) || [];
  const charted = new Set(panels.flat());

  const thead = document.createElement("thead");
  const header = document.createElement("tr");
  header.dataset.hover = `loop:${loop.loop_id}`;
  const rowLabel = document.createElement("th");
  rowLabel.className = "liveedit-rowlabel";
  header.append(rowLabel);
  for (const column of cols) {
    const th = document.createElement("th");
    th.dataset.var = column;
    // Only top-level loops support charting (nested loop data is sparser).
    if (!nested && numerics[column]) {
      th.classList.add("liveedit-chart-col");
      th.dataset.chartCol = column;
      th.dataset.loop = loop.loop_id;
      th.title = `Plot ${column} — ⌘/Ctrl-click to overlay, Shift-click to stack below`;
      if (charted.has(column)) th.classList.add("liveedit-chart-col-active");
      th.append(span("liveedit-th-label", column));
      th.append(chartIcon());
    } else {
      th.textContent = column;
    }
    header.append(th);
  }
  const spacer = document.createElement("th");
  spacer.className = "liveedit-spacer";
  header.append(spacer);
  thead.append(header);
  table.append(thead);

  const tbody = document.createElement("tbody");
  (loop.passes || []).forEach((pass, index) => {
    const row = document.createElement("tr");
    row.dataset.hover = `loop:${loop.loop_id}`;
    if (pass.failed) row.classList.add("liveedit-pass-error");
    const label = document.createElement("td");
    label.className = "liveedit-rowlabel";
    label.textContent = pass.failed ? `✗ pass ${index + 1}` : `pass ${index + 1}`;
    row.append(label);

    for (const column of cols) {
      const cell = document.createElement("td");
      cell.dataset.var = column;
      const reprValue = pass.cells?.[column] ?? "";
      const html = pass.cells_html?.[column];
      if (html != null && html !== "") {
        cell.classList.add("liveedit-html");
        cell.innerHTML = html;
      } else {
        cell.textContent = reprValue;
      }
      cell.title = reprValue;
      if ((pass.changed || []).includes(column)) {
        cell.classList.add("liveedit-changed");
      }
      row.append(cell);
    }
    const spacerCell = document.createElement("td");
    spacerCell.className = "liveedit-spacer";
    row.append(spacerCell);
    tbody.append(row);

    if (pass.children?.length) {
      const childRow = document.createElement("tr");
      childRow.className = "liveedit-child-row";
      const childCell = document.createElement("td");
      childCell.colSpan = cols.length + 2;
      childCell.className = "liveedit-child-cell";
      for (const child of pass.children) {
        childCell.append(loopBlock(child, chartState, colVisible, true));
      }
      childRow.append(childCell);
      tbody.append(childRow);
    }
  });
  table.append(tbody);
  return table;
}

function loopBlock(loop, chartState, colVisible, nested = false) {
  const block = document.createElement("div");
  block.className = nested ? "liveedit-loopblock liveedit-loopblock-nested" : "liveedit-loopblock";
  block.dataset.loop = loop.loop_id;

  const badgeRow = document.createElement("div");
  badgeRow.className = "liveedit-badgerow";
  badgeRow.dataset.hover = `loop:${loop.loop_id}`;
  const badge = span(`liveedit-badge ${loop.loop_type === "for" ? "liveedit-for" : "liveedit-while"}`, `${loop.loop_type} loop`);
  badgeRow.append(badge);
  block.append(badgeRow);

  const table = tableForLoop(loop, chartState, colVisible, nested);
  const numerics = loop.numerics || {};
  const panels = chartState.get(loop.loop_id) || [];
  // Keep only chartable, visible columns and drop panels that end up empty.
  const activePanels = panels
    .map((columns) => columns.filter((column) => numerics[column] && colVisible(column)))
    .filter((columns) => columns.length);

  if (!nested && activePanels.length) {
    block.classList.add("liveedit-loopblock-charting");
    const body = document.createElement("div");
    body.className = "liveedit-loopbody";
    body.append(table);
    body.append(chartPanel(loop, activePanels));
    block.append(body);
  } else {
    block.append(table);
  }
  return block;
}

const SVG_NS = "http://www.w3.org/2000/svg";

function svgEl(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    node.setAttribute(key, String(value));
  }
  return node;
}

function formatTick(value) {
  if (Number.isInteger(value)) return String(value);
  const abs = Math.abs(value);
  if (abs >= 100) return value.toFixed(0);
  if (abs >= 1) return value.toFixed(1);
  return value.toFixed(2);
}

function chartLegend(columns) {
  const legend = document.createElement("div");
  legend.className = "liveedit-chart-legend";
  columns.forEach((column, index) => {
    const item = document.createElement("span");
    item.className = `liveedit-chart-legend-item liveedit-chart-swatch-${index % CHART_PALETTE_SIZE}`;
    item.textContent = column;
    legend.append(item);
  });
  return legend;
}

function chartPanel(loop, activePanels) {
  const panel = document.createElement("div");
  panel.className = "liveedit-chart";

  const close = document.createElement("button");
  close.type = "button";
  close.className = "liveedit-chart-close";
  close.dataset.loop = loop.loop_id;
  close.textContent = "×";
  close.title = "Clear chart";
  panel.append(close);

  // One chart per panel, stacked vertically. They share the X pixel mapping, so
  // iterations line up; only the bottom panel labels the shared X-axis.
  const stack = document.createElement("div");
  stack.className = "liveedit-chart-stack";
  activePanels.forEach((columns, index) => {
    const block = document.createElement("div");
    block.className = "liveedit-chart-block";
    block.append(chartSvg(loop, columns, index === activePanels.length - 1));
    block.append(chartLegend(columns));
    stack.append(block);
  });
  panel.append(stack);
  return panel;
}

function chartSvg(loop, columns, showX) {
  const width = 280;
  const margin = { top: 10, right: 10, bottom: 22, left: 40 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = 110;
  const height = margin.top + plotHeight + margin.bottom;

  const series = columns.map((column) => loop.numerics[column]);
  const passCount = series[0].length;

  let min = Infinity;
  let max = -Infinity;
  for (const values of series) {
    for (const value of values) {
      if (value < min) min = value;
      if (value > max) max = value;
    }
  }
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    min = 0;
    max = 1;
  }
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const yPad = (max - min) * 0.05;
  min -= yPad;
  max += yPad;

  const xFor = (index) =>
    margin.left + (passCount <= 1 ? plotWidth / 2 : (index / (passCount - 1)) * plotWidth);
  const yFor = (value) =>
    margin.top + plotHeight - ((value - min) / (max - min)) * plotHeight;

  const svg = svgEl("svg", {
    class: "liveedit-chart-svg",
    width,
    height,
    viewBox: `0 0 ${width} ${height}`,
  });

  const baseY = margin.top + plotHeight;
  const baseX = margin.left;

  // Y ticks + gridlines.
  const yTicks = 5;
  for (let i = 0; i < yTicks; i++) {
    const value = min + (i / (yTicks - 1)) * (max - min);
    const y = yFor(value);
    svg.append(
      svgEl("line", {
        class: "liveedit-chart-grid",
        x1: baseX,
        y1: y,
        x2: baseX + plotWidth,
        y2: y,
      })
    );
    const label = svgEl("text", {
      class: "liveedit-chart-axis-label",
      x: baseX - 5,
      y: y + 3,
      "text-anchor": "end",
    });
    label.textContent = formatTick(value);
    svg.append(label);
  }

  // X ticks: one per pass, thinned to at most 6 labels. Only the bottom panel
  // in a stack labels the shared X-axis to keep the others compact.
  if (showX) {
    const stride = Math.max(1, Math.ceil(passCount / 6));
    for (let i = 0; i < passCount; i++) {
      if (i % stride !== 0 && i !== passCount - 1) continue;
      const x = xFor(i);
      svg.append(
        svgEl("line", {
          class: "liveedit-chart-tick",
          x1: x,
          y1: baseY,
          x2: x,
          y2: baseY + 3,
        })
      );
      const label = svgEl("text", {
        class: "liveedit-chart-axis-label",
        x,
        y: baseY + 14,
        "text-anchor": "middle",
      });
      label.textContent = String(i + 1);
      svg.append(label);
    }
  }

  // Axis baselines.
  svg.append(
    svgEl("line", { class: "liveedit-chart-axis", x1: baseX, y1: margin.top, x2: baseX, y2: baseY })
  );
  svg.append(
    svgEl("line", { class: "liveedit-chart-axis", x1: baseX, y1: baseY, x2: baseX + plotWidth, y2: baseY })
  );

  // One line + points per selected column.
  series.forEach((values, seriesIndex) => {
    const paletteIndex = seriesIndex % CHART_PALETTE_SIZE;
    const points = values.map((value, index) => `${xFor(index)},${yFor(value)}`).join(" ");
    svg.append(
      svgEl("polyline", {
        class: `liveedit-chart-line liveedit-chart-stroke-${paletteIndex}`,
        points,
        fill: "none",
      })
    );
    values.forEach((value, index) => {
      const dot = svgEl("circle", {
        class: `liveedit-chart-dot liveedit-chart-fill-${paletteIndex}`,
        cx: xFor(index),
        cy: yFor(value),
        r: 2.5,
      });
      const title = svgEl("title", {});
      title.textContent = `${columns[seriesIndex]} · pass ${index + 1} = ${formatTick(value)}`;
      dot.append(title);
      svg.append(dot);
    });
  });

  return svg;
}

function clearAll(root) {
  root.querySelectorAll(
    ".liveedit-var-active,.liveedit-line-assign,.liveedit-col-active,.liveedit-return-active,.liveedit-loop-d1,.liveedit-loop-d2,.liveedit-loop-lit,.liveedit-loop-active"
  ).forEach((el) => {
    el.classList.remove(
      "liveedit-var-active",
      "liveedit-line-assign",
      "liveedit-col-active",
      "liveedit-return-active",
      "liveedit-loop-d1",
      "liveedit-loop-d2",
      "liveedit-loop-lit",
      "liveedit-loop-active"
    );
  });
}

function activateVar(root, name) {
  root.querySelectorAll(`[data-var="${CSS.escape(name)}"]`).forEach((el) => {
    if (el.classList.contains("liveedit-var") || el.classList.contains("liveedit-kv")) {
      el.classList.add("liveedit-var-active");
    }
    if (el.classList.contains("liveedit-return")) {
      el.classList.add("liveedit-return-active");
    }
    if (el.tagName === "TD" || el.tagName === "TH") {
      el.classList.add("liveedit-col-active");
    }
  });
  root.querySelectorAll(".liveedit-line[data-assigns]").forEach((line) => {
    if (line.dataset.assigns.split(/\s+/).includes(name)) {
      line.classList.add("liveedit-line-assign");
    }
  });
  root.querySelectorAll(".liveedit-line[data-return]").forEach((line) => {
    if (line.dataset.return.split(/\s+/).includes(name)) {
      line.classList.add("liveedit-line-assign");
    }
  });
}

function activateLoopSet(root, chain) {
  root.querySelectorAll(".liveedit-line[data-loop-body]").forEach((line) => {
    const membership = line.dataset.loopBody.split(/\s+/);
    const depth = membership.filter((id) => chain.includes(id)).length;
    if (depth >= 2) line.classList.add("liveedit-loop-d2");
    else if (depth === 1) line.classList.add("liveedit-loop-d1");
  });
  root.querySelectorAll(".liveedit-loopblock[data-loop]").forEach((block) => {
    if (chain.includes(block.dataset.loop)) block.classList.add("liveedit-loop-lit");
  });
}

function loopChainFor(el) {
  const chain = [];
  let node = el.closest(".liveedit-loopblock");
  while (node) {
    if (node.dataset.loop) chain.push(node.dataset.loop);
    node = node.parentElement && node.parentElement.closest(".liveedit-loopblock");
  }
  return chain;
}

function applyHover(root, target) {
  const token = target.closest("[data-var]");
  if (token) {
    activateVar(root, token.dataset.var);
    const chain = loopChainFor(token);
    if (chain.length) activateLoopSet(root, chain);
    return;
  }

  const row = target.closest("[data-hover]");
  if (!row) return;
  const hover = row.dataset.hover;
  if (hover.startsWith("var:")) {
    activateVar(root, hover.slice(4));
    const chain = loopChainFor(row);
    if (chain.length) activateLoopSet(root, chain);
  } else if (hover.startsWith("loop:")) {
    activateLoopSet(root, hover.slice(5).split(/\s+/));
  }
}

function draw({ model, root, chartState }) {
  root.innerHTML = "";
  root.className = "liveedit-root";
  root.dataset.theme = model.get("theme") || "auto";
  // Grow horizontally to fit content (the host page scrolls); a positive width
  // caps it and turns on an internal horizontal scrollbar instead. Height stays
  // bounded via --liveedit-height so the code/trace panels scroll independently
  // and the function stays visible while the trace scrolls.
  const widthCap = model.get("width");
  root.style.width = "max-content";
  root.style.maxWidth = widthCap > 0 ? `${widthCap}px` : "none";
  root.style.overflowX = widthCap > 0 ? "auto" : "visible";
  root.style.setProperty("--liveedit-height", `${model.get("height")}px`);

  const card = document.createElement("div");
  card.className = "liveedit-card";

  const error = model.get("error");

  const codePanel = document.createElement("div");
  codePanel.className = "liveedit-code";
  const annotations = model.get("annotations") || { lines: [] };
  const codeLines = [];
  for (const line of annotations.lines || []) {
    const row = codeLine(line);
    codePanel.append(row);
    codeLines.push(row);
  }
  if (error && error.lineno) {
    const failingLine = codeLines[error.lineno - 1];
    if (failingLine) {
      failingLine.classList.add("liveedit-line-error");
      const inline = document.createElement("div");
      inline.className = "liveedit-inline-error";
      inline.textContent = `${error.type}: ${error.message}`;
      failingLine.after(inline);
    }
  }

  const tracePanel = document.createElement("div");
  tracePanel.className = "liveedit-trace";
  if (error) {
    const errorBox = document.createElement("div");
    errorBox.className = "liveedit-error";
    errorBox.textContent = `${error.type}: ${error.message}`;
    tracePanel.append(errorBox);
  }

  const trace = model.get("trace") || {};
  const setup = document.createElement("div");
  setup.className = "liveedit-kv-block";
  for (const item of trace.setup || []) setup.append(kvRow(item));
  tracePanel.append(setup);

  // Empty visible_columns means "show everything".
  const visible = new Set(model.get("visible_columns") || []);
  const colVisible = (column) => visible.size === 0 || visible.has(column);

  for (const loop of trace.body || []) {
    tracePanel.append(loopBlock(loop, chartState, colVisible));
  }

  const returned = returnChip(trace.returned, error);
  if (trace.returned?.repr) {
    for (const line of annotations.lines || []) {
      for (const name of line.returns || []) {
        returned.dataset.var = name;
        returned.dataset.hover = `var:${name}`;
        break;
      }
      if (returned.dataset.var) break;
    }
  }
  tracePanel.append(returned);

  card.append(codePanel, tracePanel);
  root.append(card);
}

function render({ model, el }) {
  const root = document.createElement("div");
  el.append(root);
  // loop_id -> Set of column names the user selected for charting.
  const chartState = new Map();
  const redraw = () => draw({ model, root, chartState });
  redraw();

  // A full redraw rebuilds the DOM, which resets scroll. Preserve the scroll
  // position of the panels so toggling a chart doesn't jump the view.
  const redrawKeepingScroll = () => {
    const selectors = [".liveedit-trace", ".liveedit-code"];
    const saved = selectors.map((selector) => {
      const el = root.querySelector(selector);
      return el ? { selector, left: el.scrollLeft, top: el.scrollTop } : null;
    });
    const rootLeft = root.scrollLeft;
    const rootTop = root.scrollTop;
    redraw();
    root.scrollLeft = rootLeft;
    root.scrollTop = rootTop;
    for (const entry of saved) {
      if (!entry) continue;
      const el = root.querySelector(entry.selector);
      if (el) {
        el.scrollLeft = entry.left;
        el.scrollTop = entry.top;
      }
    }
  };

  root.addEventListener("mouseover", (event) => {
    clearAll(root);
    applyHover(root, event.target);
  });
  root.addEventListener("mouseleave", () => clearAll(root));

  root.addEventListener("click", (event) => {
    const header = event.target.closest("th[data-chart-col]");
    if (header) {
      const loopId = header.dataset.loop;
      const column = header.dataset.chartCol;
      const panels = (chartState.get(loopId) || []).map((columns) => [...columns]);
      if (event.shiftKey) {
        // Shift-click: add a new chart stacked below, sharing the X-axis.
        panels.push([column]);
      } else if (event.metaKey || event.ctrlKey) {
        // ⌘/Ctrl-click: overlay onto the current (bottom) chart, shared Y-axis.
        const last = panels[panels.length - 1];
        if (!last) {
          panels.push([column]);
        } else {
          const at = last.indexOf(column);
          if (at >= 0) last.splice(at, 1);
          else last.push(column);
          if (!last.length) panels.pop();
        }
      } else {
        // Plain click: one fresh single-series chart (toggles off if it's the
        // only series currently shown).
        const isSole =
          panels.length === 1 && panels[0].length === 1 && panels[0][0] === column;
        panels.length = 0;
        if (!isSole) panels.push([column]);
      }
      if (panels.length) chartState.set(loopId, panels);
      else chartState.delete(loopId);
      redrawKeepingScroll();
      return;
    }
    const close = event.target.closest(".liveedit-chart-close");
    if (close) {
      chartState.delete(close.dataset.loop);
      redrawKeepingScroll();
    }
  });

  // Editing code changes loop ids/columns, so drop selections that no longer apply.
  model.on("change:trace", () => chartState.clear());

  ["code", "trace", "annotations", "error", "theme", "width", "height", "visible_columns"].forEach((name) => {
    model.on(`change:${name}`, redraw);
  });
}

export default { render };
