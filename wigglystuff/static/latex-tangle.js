// Keep in step with the KaTeX CSS marimo adopts into widget shadow roots
// (0.18 renamed .sizing to .katex-sizing; a mismatch collapses nested scripts).
const KATEX_VERSION = "0.18.7";
const KATEX_MODULE_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.mjs`;
const KATEX_CSS_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css`;
const SVGNS = "http://www.w3.org/2000/svg";

// Note layout, in px.
const NOTE_PAD_X = 16; // air left and right of the labels
const NOTE_PAD_Y = 16; // stage border to a label row
const NOTE_ARROW_SPACE = 30; // formula to a label row
const NOTE_GAP = 16; // between two labels in a row
const NOTE_CLEARANCE = 3; // between an arrow end and what it touches
const HEAD_LENGTH = 7;
const HEAD_HALF_WIDTH = 4;

let katexPromise = null;

function loadKatex() {
  if (!katexPromise) katexPromise = import(KATEX_MODULE_URL);
  return katexPromise;
}

function katexCssLink() {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = KATEX_CSS_URL;
  link.dataset.latexTangleKatex = "true";
  return link;
}

// The document copy provides the @font-face rules (fonts don't load from
// inside a shadow root); a second copy next to the widget styles the markup
// when the widget lives in a shadow root that document styles can't reach.
function ensureKatexCss() {
  if (document.querySelector('link[data-latex-tangle-katex="true"]')) return;
  document.head.appendChild(katexCssLink());
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Note text is plain text with inline $math$ and **bold**. Odd-indexed parts
// of the split are the math pieces.
function noteHtml(katex, text) {
  return text
    .split(/\$([^$]+)\$/)
    .map((part, i) => {
      if (i % 2 === 1) return katex.renderToString(part, { throwOnError: false });
      return escapeHtml(part).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    })
    .join("");
}

// Spread labels along one row: each wants to sit centered on its term, but
// may not overlap its neighbours or leave [minX, maxX].
function packRow(items, minX, maxX) {
  for (const item of items) item.x = item.cx - item.w / 2;
  for (let i = 0; i < items.length; i++) {
    const floor = i === 0 ? minX : items[i - 1].x + items[i - 1].w + NOTE_GAP;
    items[i].x = Math.max(items[i].x, floor);
  }
  for (let i = items.length - 1; i >= 0; i--) {
    const ceiling = i === items.length - 1 ? maxX : items[i + 1].x - NOTE_GAP;
    items[i].x = Math.max(minX, Math.min(items[i].x, ceiling - items[i].w));
  }
}

// A gentle S-curve that leaves the label and lands on the term vertically:
// straight when the label sits right above or below its term.
function arrowPaths(from, to) {
  const midY = (from.y + to.y) / 2;
  const arc =
    `M ${from.x} ${from.y} C ${from.x} ${midY} ${to.x} ${midY} ${to.x} ${to.y}`;
  const dir = Math.sign(to.y - from.y) || 1;
  const backY = to.y - dir * HEAD_LENGTH;
  const head =
    `M ${to.x - HEAD_HALF_WIDTH} ${backY} L ${to.x} ${to.y} ` +
    `L ${to.x + HEAD_HALF_WIDTH} ${backY}`;
  return [arc, head];
}

// The screen box of a term, built from what is actually drawn: glyphs,
// fraction bars and SVG pieces. The wrapper span's own rect is no good:
// KaTeX lays out fractions and scripts with offset children that overflow it.
function termRect(term) {
  const rects = [];
  const range = document.createRange();
  const walker = document.createTreeWalker(term, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!node.textContent.trim()) continue;
    range.selectNodeContents(node);
    rects.push(range.getBoundingClientRect());
  }
  for (const node of term.querySelectorAll("svg, .frac-line, .rule, .hline")) {
    rects.push(node.getBoundingClientRect());
  }
  const drawn = rects.filter((r) => r.width > 0 && r.height > 0);
  if (!drawn.length) return term.getBoundingClientRect();
  const left = Math.min(...drawn.map((r) => r.left));
  const top = Math.min(...drawn.map((r) => r.top));
  const right = Math.max(...drawn.map((r) => r.right));
  const bottom = Math.max(...drawn.map((r) => r.bottom));
  return { left, top, right, bottom, width: right - left, height: bottom - top };
}

function formatValue(value, digits) {
  const safe = Math.abs(value) < 10 ** (-(digits + 1)) ? 0 : value;
  return safe.toFixed(digits);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function roundForStep(value, step) {
  const precision = Math.max(0, (String(step).split(".")[1] || "").length);
  return Number(value.toFixed(precision + 2));
}

function snap(value, spec) {
  const snapped =
    spec.min_value + Math.round((value - spec.min_value) / spec.step) * spec.step;
  return roundForStep(clamp(snapped, spec.min_value, spec.max_value), spec.step);
}

async function render({ model, el }) {
  ensureKatexCss();
  let katex;
  try {
    const module = await loadKatex();
    katex = module.default || module;
  } catch (error) {
    const message = `Unable to load KaTeX ${KATEX_VERSION}: ${String(error)}`;
    el.textContent = message;
    model.set("error", message);
    model.save_changes();
    return;
  }

  const root = document.createElement("div");
  root.className = `latex-tangle latex-tangle--theme-${model.get("theme")}`;
  const stage = document.createElement("div");
  stage.className = "latex-tangle__stage";
  const formulaHost = document.createElement("div");
  formulaHost.className = "latex-tangle__formula";
  const tints = document.createElementNS(SVGNS, "svg");
  tints.setAttribute("class", "latex-tangle__tints");
  const arrows = document.createElementNS(SVGNS, "svg");
  arrows.setAttribute("class", "latex-tangle__arrows");
  const footer = document.createElement("div");
  footer.className = "latex-tangle__footer";
  const reset = document.createElement("button");
  reset.className = "latex-tangle__reset";
  reset.type = "button";
  reset.textContent = "Reset";
  const errorBox = document.createElement("div");
  errorBox.className = "latex-tangle__error";
  errorBox.hidden = true;

  stage.appendChild(tints);
  stage.appendChild(formulaHost);
  stage.appendChild(arrows);
  footer.appendChild(reset);
  root.appendChild(stage);
  root.appendChild(footer);
  root.appendChild(errorBox);
  const cssLink = katexCssLink();
  el.replaceChildren(cssLink, root);

  let drag = null;
  let activeEditor = null;
  let editingName = null;
  let disposed = false;
  let localValuesUpdate = false;
  let saveTimer = null;
  let initialValues = getInitialValues();
  let labels = {}; // annotation name -> label div

  function getParameters() {
    return model.get("parameters") || {};
  }

  function getInitialValues() {
    return Object.fromEntries(
      Object.entries(model.get("parameters") || {}).map(([name, spec]) => [
        name,
        spec.value,
      ]),
    );
  }

  function setError(message) {
    const current = model.get("error");
    errorBox.textContent = message;
    errorBox.hidden = !message;
    if (current === message) return;
    model.set("error", message);
    model.save_changes();
  }

  function showValue(name, spec) {
    if (spec.display === "number") return true;
    if (editingName === name) return true;
    if (!drag) return false;
    if (!drag.moved) return drag.name === name;
    return model.get("reveal_all_on_drag") || drag.name === name;
  }

  function parameterTex(name) {
    const parameters = getParameters();
    const spec = parameters[name];
    const values = model.get("values") || {};
    if (!spec || !(name in values)) {
      throw new Error(`Unknown TangleLatex parameter: ${name}`);
    }
    const content = showValue(name, spec)
      ? formatValue(values[name], spec.digits)
      : spec.symbol;
    return String.raw`\htmlData{tangle-param=${name}}{${content}}`;
  }

  function renderFormula() {
    if (disposed) return;
    try {
      const source = model
        .get("latex")
        .replace(/\\tangle\{([A-Za-z][A-Za-z0-9_-]*)\}/g, (_, name) =>
          parameterTex(name),
        );
      katex.render(source, formulaHost, {
        displayMode: model.get("display_mode"),
        throwOnError: true,
        macros: { "\\note": "\\htmlData{note=#1}{#2}" },
        trust: (context) => context.command === "\\htmlData",
        strict: (errorCode) => (errorCode === "htmlExtension" ? "ignore" : "warn"),
      });
      setError("");
    } catch (error) {
      formulaHost.replaceChildren();
      tints.replaceChildren();
      arrows.replaceChildren();
      setError(error instanceof Error ? error.message : String(error));
      return;
    }

    const parameters = getParameters();
    const values = model.get("values") || {};
    for (const [name, spec] of Object.entries(parameters)) {
      const targets = formulaHost.querySelectorAll(
        `.katex-html [data-tangle-param="${name}"]`,
      );
      for (const target of targets) {
        target.tabIndex = 0;
        target.setAttribute("role", "button");
        target.style.setProperty("--lt-param-light", spec.color.light);
        target.style.setProperty("--lt-param-dark", spec.color.dark);
        target.setAttribute(
          "aria-label",
          `${spec.label}: ${formatValue(values[name], spec.digits)}. Drag horizontally or press Enter to type.`,
        );
        if (drag && drag.name === name) target.classList.add("is-active");
      }
    }
    spaceNumbersAfterDigits();
    for (const [name, note] of Object.entries(getNotes())) {
      for (const term of termsFor(name)) {
        term.classList.add("latex-tangle__note-term");
        term.tabIndex = 0;
        term.setAttribute("aria-label", note.text);
        colorize(term, note.color);
      }
    }
    layoutNotes();
  }

  function getNotes() {
    return model.get("notes") || {};
  }

  // A revealed number right after a digit reads as one number: 2σ² with
  // σ = 1.7 shows as "21.7²". Walk the drawn text in order and give such a
  // number a small gap on its left.
  function spaceNumbersAfterDigits() {
    const html = formulaHost.querySelector(".katex-html");
    if (!html) return;
    const walker = document.createTreeWalker(html, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    let previous = "";
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.textContent.trim();
      if (!text) continue;
      const param = node.parentElement.closest("[data-tangle-param]");
      if (param && !seen.has(param)) {
        seen.add(param);
        const gap = /[0-9.]$/.test(previous) && /^[0-9.]/.test(text);
        param.classList.toggle("latex-tangle__param--gap", gap);
      }
      previous = text;
    }
  }

  // Every part marked with \note{name}{...}, as a list.
  function annotations() {
    return Object.entries(getNotes()).map(([name, note]) => ({ name, ...note }));
  }

  function termsFor(name) {
    return formulaHost.querySelectorAll(`.katex-html [data-note="${name}"]`);
  }

  // The note that explains a parameter: the one wrapping exactly that
  // parameter (\note{width}{\tangle{sigma}}), wherever it sits.
  function noteForParam(param) {
    const match = annotations().find((note) => note.param === param);
    return match ? match.name : "";
  }

  function colorize(node, color) {
    node.style.setProperty("--lt-note-light", color.light);
    node.style.setProperty("--lt-note-dark", color.dark);
  }

  function buildLabels() {
    for (const label of Object.values(labels)) label.remove();
    labels = {};
    for (const note of annotations()) {
      const label = document.createElement("div");
      label.className = "latex-tangle__label";
      label.dataset.annotation = note.name;
      label.innerHTML = noteHtml(katex, note.text);
      colorize(label, note.color);
      stage.appendChild(label);
      labels[note.name] = label;
    }
  }

  function layoutNotes() {
    if (disposed) return;
    tints.replaceChildren();
    arrows.replaceChildren();
    const notes = annotations();
    if (!notes.length) {
      stage.style.paddingTop = "";
      stage.style.paddingBottom = "";
      applyHover();
      return;
    }
    const stageWidth = stage.clientWidth;
    const relative = (rect) => {
      const base = stage.getBoundingClientRect();
      return {
        left: rect.left - base.left,
        right: rect.right - base.left,
        top: rect.top - base.top,
        bottom: rect.bottom - base.top,
        cx: rect.left - base.left + rect.width / 2,
        cy: rect.top - base.top + rect.height / 2,
      };
    };

    // 1. Pick a side per note. "auto" sends parts above the formula's middle
    // (numerators, superscripts) up and parts below it down, and balances
    // the rest.
    const formulaBox = relative(formulaHost.getBoundingClientRect());
    const items = [];
    const counts = { top: 0, bottom: 0 };
    const undecided = [];
    for (const note of notes) {
      const term = termsFor(note.name)[0];
      const label = labels[note.name];
      if (!term || !label) continue;
      const box = relative(termRect(term));
      const item = { ...note, term, label, cx: box.cx };
      item.w = label.offsetWidth;
      item.h = label.offsetHeight;
      items.push(item);
      if (item.side === "auto") {
        const offset = box.cy - formulaBox.cy;
        if (offset < -4) item.side = "top";
        else if (offset > 4) item.side = "bottom";
        else undecided.push(item);
      }
      if (item.side !== "auto") counts[item.side] += 1;
    }
    for (const item of undecided) {
      item.side = counts.top <= counts.bottom ? "top" : "bottom";
      counts[item.side] += 1;
    }

    // 2. One row of labels per side, in the same left-to-right order as
    // their terms, so arrows on one side never cross.
    const heights = {};
    for (const side of ["top", "bottom"]) {
      const row = items
        .filter((item) => item.side === side)
        .sort((a, b) => a.cx - b.cx);
      packRow(row, NOTE_PAD_X, stageWidth - NOTE_PAD_X);
      heights[side] = row.length ? Math.max(...row.map((item) => item.h)) : 0;
    }
    const band = (side) => (heights[side] ? NOTE_ARROW_SPACE + heights[side] : 0);
    stage.style.paddingTop = `${NOTE_PAD_Y + band("top")}px`;
    stage.style.paddingBottom = `${NOTE_PAD_Y + band("bottom")}px`;

    // 3. Padding moved the formula, so measure again and place the labels.
    const formula = relative(formulaHost.getBoundingClientRect());
    for (const item of items) {
      const top =
        item.side === "top"
          ? formula.top - NOTE_ARROW_SPACE - item.h
          : formula.bottom + NOTE_ARROW_SPACE;
      item.label.style.left = `${item.x}px`;
      item.label.style.top = `${top}px`;
    }

    // 4. A soft tint behind each fixed part (parameters have their own
    // styling). Outer parts come first in document order, so nested tints
    // stack on top.
    for (const node of formulaHost.querySelectorAll(".katex-html [data-note]")) {
      const note = getNotes()[node.dataset.note];
      if (!note) continue;
      const box = relative(termRect(node));
      const rect = document.createElementNS(SVGNS, "rect");
      rect.setAttribute("class", "latex-tangle__tint");
      rect.dataset.annotation = node.dataset.note;
      rect.setAttribute("x", box.left - 3);
      rect.setAttribute("y", box.top - 2);
      rect.setAttribute("width", box.right - box.left + 6);
      rect.setAttribute("height", box.bottom - box.top + 4);
      rect.setAttribute("rx", 4);
      colorize(rect, note.color);
      tints.appendChild(rect);
    }

    // 5. One arrow per note, from the label edge facing the formula to the
    // first occurrence of its term.
    for (const item of items) {
      const term = relative(termRect(item.term));
      const label = relative(item.label.getBoundingClientRect());
      const fromX = Math.max(label.left + 8, Math.min(term.cx, label.right - 8));
      const top = item.side === "top";
      const from = { x: fromX, y: top ? label.bottom + NOTE_CLEARANCE : label.top - NOTE_CLEARANCE };
      const to = { x: term.cx, y: top ? term.top - NOTE_CLEARANCE : term.bottom + NOTE_CLEARANCE };
      const group = document.createElementNS(SVGNS, "g");
      group.setAttribute("class", "latex-tangle__arrow");
      group.dataset.annotation = item.name;
      colorize(group, item.color);
      for (const d of arrowPaths(from, to)) {
        const path = document.createElementNS(SVGNS, "path");
        path.setAttribute("d", d);
        group.appendChild(path);
      }
      arrows.appendChild(group);
    }
    applyHover();
  }

  // The highlighted note: the dragged parameter's note wins over the one
  // hovered. Everything else fades.
  function applyHover() {
    const name = drag ? noteForParam(drag.name) : model.get("hovered");
    const annotated = Boolean(name) && name in labels;
    root.classList.toggle("has-hover", annotated);
    for (const node of stage.querySelectorAll("[data-annotation]")) {
      node.classList.toggle("is-hovered", annotated && node.dataset.annotation === name);
    }
    for (const node of formulaHost.querySelectorAll(".katex-html [data-note]")) {
      node.classList.toggle("is-hovered", annotated && node.dataset.note === name);
    }
  }

  function setHovered(name) {
    if (model.get("hovered") === name) return;
    model.set("hovered", name);
    model.save_changes();
    applyHover();
  }

  // `hovered` is always a note name. A parameter resolves to the note that
  // explains it, otherwise to the innermost note around it.
  function handleHover(event) {
    const label = event.target.closest("[data-annotation]");
    if (label && stage.contains(label)) return setHovered(label.dataset.annotation);
    const param = event.target.closest("[data-tangle-param]");
    const paramNote = param ? noteForParam(param.dataset.tangleParam) : "";
    if (paramNote) return setHovered(paramNote);
    const term = event.target.closest("[data-note]");
    setHovered(term && stage.contains(term) ? term.dataset.note : "");
  }

  function handleHoverEnd() {
    setHovered("");
  }

  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveTimer = null;
      model.save_changes();
    }, 50);
  }

  function flushSave() {
    clearTimeout(saveTimer);
    saveTimer = null;
    model.save_changes();
  }

  function updateValue(name, value, { flush = false } = {}) {
    localValuesUpdate = true;
    model.set("values", { ...(model.get("values") || {}), [name]: value });
    renderFormula();
    if (flush) flushSave();
    else scheduleSave();
  }

  function occurrenceIndex(target, name) {
    return [
      ...formulaHost.querySelectorAll(
        `.katex-html [data-tangle-param="${name}"]`,
      ),
    ].indexOf(target);
  }

  function startDrag(event) {
    const target = event.target.closest("[data-tangle-param]");
    if (!target || (event.pointerType === "mouse" && event.button !== 0)) return;
    event.preventDefault();
    const name = target.dataset.tangleParam;
    const occurrence = occurrenceIndex(target, name);
    closeEditor(false);
    const spec = getParameters()[name];
    drag = {
      name,
      occurrence,
      pointerId: event.pointerId,
      startX: event.clientX,
      startValue: (model.get("values") || {})[name],
      spec,
      moved: false,
    };
    root.classList.add("is-dragging");
    renderFormula();
  }

  function moveDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const deltaX = event.clientX - drag.startX;
    if (Math.abs(deltaX) >= 3) drag.moved = true;
    if (!drag.moved) return;
    event.preventDefault();
    const stepCount = Math.trunc(deltaX / drag.spec.pixels_per_step);
    const next = clamp(
      drag.startValue + stepCount * drag.spec.step,
      drag.spec.min_value,
      drag.spec.max_value,
    );
    const rounded = roundForStep(next, drag.spec.step);
    if ((model.get("values") || {})[drag.name] === rounded) {
      renderFormula();
      return;
    }
    updateValue(drag.name, rounded);
  }

  function endDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const finished = drag;
    drag = null;
    root.classList.remove("is-dragging");
    if (finished.moved) {
      renderFormula();
      flushSave();
      return;
    }
    openEditor(finished.name, finished.occurrence);
  }

  function cancelDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    drag = null;
    root.classList.remove("is-dragging");
    renderFormula();
  }

  function openEditor(name, occurrence = 0) {
    closeEditor(false);
    const spec = getParameters()[name];
    editingName = name;
    renderFormula();
    const targets = formulaHost.querySelectorAll(
      `.katex-html [data-tangle-param="${name}"]`,
    );
    const target = targets[Math.max(0, occurrence)] || targets[0];
    if (!target) return;

    const input = document.createElement("input");
    const editorStyle = model.get("editor");
    input.type = "text";
    input.inputMode = "decimal";
    input.className = `latex-tangle__editor latex-tangle__editor--${editorStyle}`;
    input.value = formatValue((model.get("values") || {})[name], spec.digits);
    input.setAttribute("aria-label", `Set ${spec.label}`);
    input.style.setProperty("--lt-editor-light", spec.color.light);
    input.style.setProperty("--lt-editor-dark", spec.color.dark);

    const targetRect = target.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();
    if (editorStyle === "popover") {
      input.style.left = `${targetRect.left + targetRect.width / 2 - stageRect.left}px`;
      input.style.top = `${targetRect.bottom - stageRect.top + 10}px`;
    } else {
      target.style.visibility = "hidden";
      input.style.left = `${targetRect.left + targetRect.width / 2 - stageRect.left}px`;
      input.style.top = `${targetRect.top + targetRect.height / 2 - stageRect.top}px`;
      input.style.width = `${Math.max(targetRect.width + 16, 54)}px`;
      input.style.height = `${Math.max(targetRect.height + 8, 34)}px`;
      input.style.fontSize = getComputedStyle(target).fontSize;
      input.style.transform = "translate(-50%, -50%)";
    }

    stage.appendChild(input);
    activeEditor = {
      input,
      target,
      name,
      spec,
      previous: (model.get("values") || {})[name],
    };
    input.addEventListener("keydown", handleEditorKeydown);
    input.addEventListener("blur", handleEditorBlur);
    input.focus();
    input.select();
  }

  function handleEditorKeydown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      closeEditor(true);
    } else if (event.key === "Escape") {
      event.preventDefault();
      closeEditor(false);
    }
  }

  function handleEditorBlur() {
    closeEditor(false);
  }

  function closeEditor(commit) {
    if (!activeEditor) return;
    const editor = activeEditor;
    if (commit) {
      const parsed = Number(editor.input.value);
      if (!Number.isFinite(parsed)) {
        editor.input.classList.add("is-invalid");
        editor.input.setAttribute("aria-invalid", "true");
        editor.input.focus();
        editor.input.select();
        return;
      }
      activeEditor = null;
      editingName = null;
      editor.target.style.visibility = "";
      editor.input.removeEventListener("keydown", handleEditorKeydown);
      editor.input.removeEventListener("blur", handleEditorBlur);
      editor.input.remove();
      updateValue(editor.name, snap(parsed, editor.spec), { flush: true });
      return;
    }

    activeEditor = null;
    editingName = null;
    editor.target.style.visibility = "";
    editor.input.removeEventListener("keydown", handleEditorKeydown);
    editor.input.removeEventListener("blur", handleEditorBlur);
    editor.input.remove();
    renderFormula();
  }

  function handleFormulaKeydown(event) {
    const target = event.target.closest("[data-tangle-param]");
    if (!target || (event.key !== "Enter" && event.key !== " ")) return;
    event.preventDefault();
    const name = target.dataset.tangleParam;
    openEditor(name, occurrenceIndex(target, name));
  }

  function handleReset() {
    closeEditor(false);
    drag = null;
    root.classList.remove("is-dragging");
    localValuesUpdate = true;
    model.set("values", { ...initialValues });
    renderFormula();
    flushSave();
  }

  function handleValuesChange() {
    if (localValuesUpdate) {
      localValuesUpdate = false;
      return;
    }
    renderFormula();
  }

  function handleParametersChange() {
    initialValues = getInitialValues();
    buildLabels();
    renderFormula();
  }

  function handleNotesChange() {
    buildLabels();
    renderFormula();
  }

  function handleConfigChange() {
    renderFormula();
  }

  function handleThemeChange() {
    root.classList.remove(
      "latex-tangle--theme-auto",
      "latex-tangle--theme-light",
      "latex-tangle--theme-dark",
    );
    root.classList.add(`latex-tangle--theme-${model.get("theme")}`);
  }

  const resizeObserver = new ResizeObserver(() => layoutNotes());
  resizeObserver.observe(stage);
  stage.addEventListener("pointerover", handleHover);
  stage.addEventListener("pointerleave", handleHoverEnd);
  stage.addEventListener("focusin", handleHover);
  stage.addEventListener("focusout", handleHoverEnd);
  stage.addEventListener("pointerdown", startDrag);
  stage.addEventListener("keydown", handleFormulaKeydown);
  stage.addEventListener("dragstart", (event) => event.preventDefault());
  reset.addEventListener("click", handleReset);
  document.addEventListener("pointermove", moveDrag);
  document.addEventListener("pointerup", endDrag);
  document.addEventListener("pointercancel", cancelDrag);
  model.on("change:values", handleValuesChange);
  model.on("change:parameters", handleParametersChange);
  model.on("change:notes", handleNotesChange);
  model.on("change:hovered", applyHover);
  model.on("change:latex", handleConfigChange);
  model.on("change:display_mode", handleConfigChange);
  model.on("change:editor", handleConfigChange);
  model.on("change:reveal_all_on_drag", handleConfigChange);
  model.on("change:theme", handleThemeChange);

  buildLabels();
  renderFormula();
  cssLink.addEventListener("load", () => layoutNotes());
  // KaTeX fonts arrive after the first render and change every measurement.
  if (document.fonts) document.fonts.ready.then(() => layoutNotes());
  const layoutTimers = [setTimeout(layoutNotes, 120), setTimeout(layoutNotes, 600)];

  return () => {
    disposed = true;
    clearTimeout(saveTimer);
    layoutTimers.forEach(clearTimeout);
    resizeObserver.disconnect();
    stage.removeEventListener("pointerover", handleHover);
    stage.removeEventListener("pointerleave", handleHoverEnd);
    stage.removeEventListener("focusin", handleHover);
    stage.removeEventListener("focusout", handleHoverEnd);
    closeEditor(false);
    stage.removeEventListener("pointerdown", startDrag);
    stage.removeEventListener("keydown", handleFormulaKeydown);
    reset.removeEventListener("click", handleReset);
    document.removeEventListener("pointermove", moveDrag);
    document.removeEventListener("pointerup", endDrag);
    document.removeEventListener("pointercancel", cancelDrag);
    model.off("change:values", handleValuesChange);
    model.off("change:parameters", handleParametersChange);
    model.off("change:notes", handleNotesChange);
    model.off("change:hovered", applyHover);
    model.off("change:latex", handleConfigChange);
    model.off("change:display_mode", handleConfigChange);
    model.off("change:editor", handleConfigChange);
    model.off("change:reveal_all_on_drag", handleConfigChange);
    model.off("change:theme", handleThemeChange);
  };
}

export default { render };
