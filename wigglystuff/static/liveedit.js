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

function tableForLoop(loop) {
  const table = document.createElement("table");
  table.className = "liveedit-table";

  const thead = document.createElement("thead");
  const header = document.createElement("tr");
  header.dataset.hover = `loop:${loop.loop_id}`;
  const rowLabel = document.createElement("th");
  rowLabel.className = "liveedit-rowlabel";
  header.append(rowLabel);
  for (const column of loop.columns || []) {
    const th = document.createElement("th");
    th.textContent = column;
    th.dataset.var = column;
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

    for (const column of loop.columns || []) {
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
      childCell.colSpan = (loop.columns || []).length + 2;
      childCell.className = "liveedit-child-cell";
      for (const child of pass.children) {
        childCell.append(loopBlock(child, true));
      }
      childRow.append(childCell);
      tbody.append(childRow);
    }
  });
  table.append(tbody);
  return table;
}

function loopBlock(loop, nested = false) {
  const block = document.createElement("div");
  block.className = nested ? "liveedit-loopblock liveedit-loopblock-nested" : "liveedit-loopblock";
  block.dataset.loop = loop.loop_id;

  const badgeRow = document.createElement("div");
  badgeRow.className = "liveedit-badgerow";
  badgeRow.dataset.hover = `loop:${loop.loop_id}`;
  const badge = span(`liveedit-badge ${loop.loop_type === "for" ? "liveedit-for" : "liveedit-while"}`, `${loop.loop_type} loop`);
  badgeRow.append(badge);
  block.append(badgeRow);
  block.append(tableForLoop(loop));
  return block;
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

function draw({ model, root }) {
  root.innerHTML = "";
  root.className = "liveedit-root";
  root.dataset.theme = model.get("theme") || "auto";
  root.style.width = `${model.get("width")}px`;
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

  for (const loop of trace.body || []) {
    tracePanel.append(loopBlock(loop));
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
  const redraw = () => draw({ model, root });
  redraw();

  root.addEventListener("mouseover", (event) => {
    clearAll(root);
    applyHover(root, event.target);
  });
  root.addEventListener("mouseleave", () => clearAll(root));

  ["code", "trace", "annotations", "error", "theme", "width", "height"].forEach((name) => {
    model.on(`change:${name}`, redraw);
  });
}

export default { render };
