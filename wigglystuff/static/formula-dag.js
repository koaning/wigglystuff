// FormulaDAG: rows of KaTeX formula cards (one row per DAG depth) plus an SVG
// overlay. Each arrow leaves the producer under its output symbol and lands on
// the spot where that output is used. Formulas can carry TangleLatex-style
// draggable numbers (\tangle{name}) and notes (\note{name}{tex}).

// Keep in step with static/latex-tangle.js (marimo adopts KaTeX CSS into
// widget shadow roots; a version mismatch collapses nested scripts).
const KATEX_VERSION = "0.18.7";
const KATEX_MODULE_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.mjs`;
const KATEX_CSS_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css`;
const SVGNS = "http://www.w3.org/2000/svg";
const HEAD_LEN = 7; // arrowhead length, px
const HEAD_HALF = 3.5; // arrowhead half-width, px
const LAND_GAP = 3; // gap between an arrow tip and the ink it points at
const SIDE_GAP = 12; // how far beside a formula a side-landing arrow drops
const SIDE_PAD = 4; // vertical clearance a side-landing run keeps from glyphs
const CORNER = 7; // radius of a side-landing arrow's turn
const NEAR_X = 6; // two vertical runs closer than this read as one line

// Note layout inside a card, in px (see static/latex-tangle.js).
const NOTE_PAD_Y = 4; // card edge to a label row
const NOTE_ARROW_SPACE = 22; // formula to a label row
const NOTE_GAP = 12; // between two labels in a row
const NOTE_CLEARANCE = 3; // between a note arrow end and what it touches
const NOTE_HEAD_LEN = 6;
const NOTE_HEAD_HALF = 3.5;
const LANE_CLEARANCE = 8; // labels keep this far from a DAG arrow passing by
const NOTE_SIDE_SPACE = 20; // a left-hand note's label to the output symbol

let katexPromise = null;
function loadKatex() {
  if (!katexPromise) katexPromise = import(KATEX_MODULE_URL);
  return katexPromise;
}

function katexCssLink() {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = KATEX_CSS_URL;
  link.dataset.formulaDagKatex = "true";
  return link;
}

// The document copy provides @font-face (fonts don't load from a shadow
// root); the copy next to the widget styles the markup inside the shadow root.
function ensureKatexCss() {
  if (document.querySelector('link[data-formula-dag-katex="true"]')) return;
  document.head.appendChild(katexCssLink());
}

function setColorVars(node, color) {
  node.classList.add("fd-colored");
  node.style.setProperty("--fd-c-light", color.light);
  node.style.setProperty("--fd-c-dark", color.dark);
}

// Transitive closure over a {node: [next, ...]} map.
function reach(start, next) {
  const seen = new Set();
  const todo = [start];
  while (todo.length) {
    for (const m of next[todo.pop()] || []) {
      if (!seen.has(m)) {
        seen.add(m);
        todo.push(m);
      }
    }
  }
  return seen;
}

// KaTeX's leaf spans: glyph text, rules (fraction lines), and SVGs (radicals,
// big delimiters). Struts are invisible spacers and are skipped.
function glyphLeaves(root) {
  const out = [];
  const walk = (node) => {
    if (node instanceof SVGElement) {
      out.push(node);
      return;
    }
    const cls = node.classList;
    if (cls.contains("pstrut") || cls.contains("strut") || cls.contains("vlist-s")) return;
    if (!node.children.length) {
      const r = node.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) out.push(node);
      return;
    }
    for (const child of node.children) walk(child);
  };
  walk(root);
  return out;
}

// An element's box is the font's full ascent/descent, well above and below
// the actual ink. For text, measure the glyphs on a canvas and trim the box
// to the ink so arrows land on the symbol rather than on empty space.
const measureCtx = document.createElement("canvas").getContext("2d");
function inkRect(el) {
  const r = el.getBoundingClientRect();
  const text = el.textContent;
  if (el instanceof SVGElement || !text || !text.trim()) return r;
  const cs = getComputedStyle(el);
  measureCtx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const m = measureCtx.measureText(text);
  if (!m.fontBoundingBoxAscent) return r;
  const baseline = r.top + m.fontBoundingBoxAscent;
  return {
    left: r.left,
    right: r.right,
    top: baseline - m.actualBoundingBoxAscent,
    bottom: baseline + m.actualBoundingBoxDescent,
  };
}

function union(boxes) {
  if (!boxes.length) return null;
  return {
    left: Math.min(...boxes.map((b) => b.left)),
    right: Math.max(...boxes.map((b) => b.right)),
    top: Math.min(...boxes.map((b) => b.top)),
    bottom: Math.max(...boxes.map((b) => b.bottom)),
  };
}

// Land on top of the symbol when nothing is above it; otherwise from the
// clear side (preferring the one facing the incoming arrow).
function landingSide(sym, glyphs, fromX) {
  // Anything starting higher up over the symbol's x-range covers it: a
  // fraction bar or numerator, a limit, or a radical (whose SVG also reaches
  // down past the symbol, so don't require it to end above).
  const above = glyphs.some(
    (g) => g.right > sym.left + 1 && g.left < sym.right - 1 && g.top < sym.top - 2,
  );
  if (!above) return "top";
  const rowMates = glyphs.filter((g) => g.bottom > sym.top - SIDE_PAD && g.top < sym.bottom + SIDE_PAD);
  const rightClear = !rowMates.some((g) => g.left >= sym.right - 1);
  const leftClear = !rowMates.some((g) => g.right <= sym.left + 1);
  const preferRight = fromX >= (sym.left + sym.right) / 2;
  if (rightClear && (preferRight || !leftClear)) return "right";
  if (leftClear) return "left";
  return "top";
}

// Is the notebook around `el` dark? Walk up the ancestors, crossing shadow
// roots to their hosts, and take the nearest theme marker a notebook sets
// (marimo: .dark / .light; others: data-theme, data-color-mode, JupyterLab's
// data-jp-theme-light). Fall back to the OS preference when there is none.
function resolveDark(el) {
  for (let n = el; n; n = n.parentNode || n.host) {
    if (n.nodeType !== 1) continue;
    const cls = n.classList;
    const mode = n.getAttribute("data-theme") || n.getAttribute("data-color-mode");
    const jpLight = n.getAttribute("data-jp-theme-light");
    if (cls.contains("dark") || cls.contains("dark-theme") || mode === "dark" || jpLight === "false") {
      return true;
    }
    if (cls.contains("light") || cls.contains("light-theme") || mode === "light" || jpLight === "true") {
      return false;
    }
  }
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

// Spread note labels along one row: each wants to sit centered on its term,
// may not overlap the label before it, and must clear `blocks` (the columns
// where DAG arrows pass through the label row). Take the free spot nearest
// the wanted one: the wanted spot itself, or flush against a block's side.
function packRow(items, blocks) {
  let floor = -Infinity;
  for (const item of items) {
    const want = Math.max(item.cx - item.w / 2, floor);
    const free = (x) => x >= floor && !blocks.some((b) => x < b.right && x + item.w > b.left);
    const candidates = [want, ...blocks.flatMap((b) => [b.left - item.w, b.right])].filter(free);
    item.x = candidates.length
      ? candidates.reduce((best, x) => (Math.abs(x - want) < Math.abs(best - want) ? x : best))
      : want;
    floor = item.x + item.w + NOTE_GAP;
  }
}

// Note text is plain text with inline $math$ and **bold**.
function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function noteHtml(katex, text) {
  return text
    .split(/\$([^$]+)\$/)
    .map((part, i) => {
      if (i % 2 === 1) return katex.renderToString(part, { throwOnError: false });
      return escapeHtml(part).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    })
    .join("");
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
  const snapped = spec.min_value + Math.round((value - spec.min_value) / spec.step) * spec.step;
  return roundForStep(clamp(snapped, spec.min_value, spec.max_value), spec.step);
}

function* permutations(items) {
  if (items.length <= 1) {
    yield items.slice();
    return;
  }
  for (let i = 0; i < items.length; i++) {
    const rest = [...items.slice(0, i), ...items.slice(i + 1)];
    for (const p of permutations(rest)) yield [items[i], ...p];
  }
}

// Cost of stacking the producers' tracks top to bottom in `order` inside one
// gap. A segment drops at `from`, runs along its track, drops at `to`.
// Track i above track j crosses when i's lower drop lands inside j's run, or
// j's upper drop starts inside i's run. If i's lower drop and j's upper drop
// share (almost) the same x, both run side by side between the two tracks
// and look like one line; that costs more than a crossing.
function trackCrossings(order, segsBySrc) {
  let count = 0;
  const inside = (x, s) => x > Math.min(s.from, s.to) + 1 && x < Math.max(s.from, s.to) - 1;
  for (let i = 0; i < order.length; i++) {
    for (let j = i + 1; j < order.length; j++) {
      for (const s of segsBySrc[order[i]]) {
        for (const u of segsBySrc[order[j]]) {
          if (inside(s.to, u)) count++;
          if (inside(u.from, s)) count++;
          if (Math.abs(s.to - u.from) < NEAR_X) count += 2;
        }
      }
    }
  }
  return count;
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
  el.replaceChildren(katexCssLink(), root);

  let cards = {}; // name -> card element
  let parts = {}; // name -> {stage, tex, tints, noteArrows, labels: {note: el}}
  let lanes = {}; // waypoint id -> lane element
  let rowEls = []; // row elements, top to bottom
  let rowOf = {}; // node id -> row index
  let board = null;
  let svg = null;
  let resetButton = null;
  let legend = {}; // number name -> {chip, value}
  let outputChips = {}; // formula name -> {chip, value}
  let lastSource = {}; // card -> the LaTeX it last rendered
  let linkedOutput = ""; // formula whose output is lit up everywhere
  let linked = ""; // number whose occurrences are lit up
  let edgeEls = []; // [{src, dst, els: [path, head]}]
  let blocks = {}; // card -> {top: [x], bottom: [x]}, x relative to the tex's left
  let errors = {}; // card -> KaTeX error message
  let disposed = false;
  let drag = null;
  let editor = null;
  let editingName = null;
  let suppressClick = false;
  let localValuesUpdate = false;
  let saveTimer = null;
  let relayoutQueued = false;

  const formulasByName = () => Object.fromEntries((model.get("formulas") || []).map((f) => [f.name, f]));
  const getParameters = () => model.get("parameters") || {};
  const getNotes = () => model.get("notes") || {};
  const getValues = () => model.get("values") || {};
  // interactive is absent on older states; only an explicit false is static.
  const isInteractive = () => model.get("interactive") !== false;

  function setTheme() {
    const theme = model.get("theme");
    const dark = theme === "dark" || (theme === "auto" && resolveDark(el));
    root.classList.add("formula-dag");
    root.classList.toggle("formula-dag--dark", dark);
    root.classList.toggle("formula-dag--light", !dark);
  }

  function applyInteractive() {
    root.classList.toggle("formula-dag--static", !isInteractive());
  }

  // ---- building -----------------------------------------------------------

  function build() {
    setTheme();
    applyInteractive();
    closeEditor(false);
    const byName = formulasByName();
    cards = {};
    parts = {};
    lastSource = {};
    lanes = {};
    rowEls = [];
    rowOf = {};
    blocks = {};
    errors = {};
    board = document.createElement("div");
    board.className = "formula-dag__board";

    for (const layer of model.get("layers") || []) {
      const row = document.createElement("div");
      row.className = "formula-dag__row";
      layer.forEach((id) => (rowOf[id] = rowEls.length));
      rowEls.push(row);
      for (const id of layer) {
        if (!byName[id]) {
          // An invisible lane reserved for an edge that skips this row.
          const lane = document.createElement("div");
          lane.className = "formula-dag__lane";
          lanes[id] = lane;
          row.appendChild(lane);
          continue;
        }
        row.appendChild(buildCard(byName[id]));
      }
      board.appendChild(row);
    }

    svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "formula-dag__edges");
    board.appendChild(svg);
    const children = [board];
    resetButton = null;
    legend = {};
    outputChips = {};
    const hasParams = Object.keys(getParameters()).length > 0;
    const hasOutputs = (model.get("formulas") || []).some((f) => f.has_fn);
    if (hasParams || (hasOutputs && model.get("legend"))) {
      const footer = document.createElement("div");
      footer.className = "formula-dag__footer";
      if (model.get("legend")) footer.appendChild(buildLegend());
      children.push(footer);
    }
    if (hasParams) {
      const footer = children[children.length - 1];
      resetButton = document.createElement("button");
      resetButton.type = "button";
      resetButton.className = "formula-dag__reset";
      resetButton.textContent = "Reset";
      resetButton.addEventListener("click", handleReset);
      footer.appendChild(resetButton);
    }
    root.replaceChildren(...children);
    Object.keys(cards).forEach(renderCard);
    renderOutputs();
    showSelected();
    relayout();
  }

  // The legend strip: one chip per number, with its symbol, what it means
  // (its `label`), and its live value. A chip scrubs and edits like the
  // number in a formula, and hovering it lights up every occurrence.
  function buildLegend() {
    const strip = document.createElement("div");
    strip.className = "formula-dag__legend";
    const inputs = document.createElement("div");
    inputs.className = "formula-dag__legend-row";
    const ordered = Object.entries(getParameters()).sort((a, b) => a[1].order - b[1].order);
    for (const [name, p] of ordered) {
      const chip = document.createElement("div");
      chip.className = "formula-dag__chip";
      chip.dataset.tangleParam = name;
      chip.tabIndex = 0;
      chip.setAttribute("role", "button");
      const symbol = document.createElement("span");
      symbol.className = "formula-dag__chip-symbol";
      symbol.innerHTML = katex.renderToString(p.symbol, { throwOnError: false });
      chip.appendChild(symbol);
      // TangleLatex's default label is "parameter <name>": not worth showing.
      if (p.label !== `parameter ${name}`) {
        const meaning = document.createElement("span");
        meaning.className = "formula-dag__chip-label";
        meaning.textContent = p.label;
        chip.appendChild(meaning);
      }
      const value = document.createElement("span");
      value.className = "formula-dag__chip-value";
      setColorVars(value, p.color);
      chip.appendChild(value);
      inputs.appendChild(chip);
      legend[name] = { chip, value };
    }
    if (inputs.children.length) strip.appendChild(inputs);
    // Then, after an arrow, one read-only chip per computed formula.
    const computed = (model.get("formulas") || []).filter((f) => f.has_fn);
    if (computed.length) {
      const results = document.createElement("div");
      results.className = "formula-dag__legend-row";
      strip.appendChild(results);
      for (const f of computed) {
        const chip = document.createElement("div");
        chip.className = "formula-dag__chip formula-dag__chip--output";
        chip.dataset.fdagLink = f.name;
        const symbol = document.createElement("span");
        symbol.className = "formula-dag__chip-symbol";
        symbol.innerHTML = katex.renderToString(f.symbol, { throwOnError: false });
        setColorVars(symbol, f.color);
        chip.appendChild(symbol);
        if (f.label !== f.name) {
          const meaning = document.createElement("span");
          meaning.className = "formula-dag__chip-label";
          meaning.textContent = f.label;
          chip.appendChild(meaning);
        }
        const value = document.createElement("span");
        value.className = "formula-dag__chip-output";
        chip.appendChild(value);
        results.appendChild(chip);
        outputChips[f.name] = { chip, value };
      }
    }
    renderLegend();
    return strip;
  }

  function renderLegend() {
    const params = getParameters();
    const values = getValues();
    for (const [name, { chip, value }] of Object.entries(legend)) {
      const p = params[name];
      value.textContent = formatValue(values[name], p.digits);
      chip.setAttribute(
        "aria-label",
        isInteractive()
          ? `${p.label}: ${value.textContent}. Drag horizontally or press Enter to type.`
          : `${p.label}: ${value.textContent}`,
      );
      chip.classList.toggle("is-active", Boolean(drag && drag.name === name));
    }
  }

  // A computed formula's value as text ("—" while it has none).
  function outputText(name) {
    const v = (model.get("outputs") || {})[name];
    return v === null || v === undefined ? "—" : formatValue(v, formulasByName()[name].digits);
  }

  // Computed values: always in the output chips; in the formulas only while
  // a number they depend on is being changed.
  function renderOutputs() {
    const errs = model.get("output_errors") || {};
    for (const [name, { chip, value }] of Object.entries(outputChips)) {
      value.textContent = outputText(name);
      chip.title = errs[name] || "";
      chip.classList.toggle("is-error", Boolean(errs[name]));
    }
    renderAll();
  }

  function buildCard(spec) {
    const id = spec.name;
    const card = document.createElement("div");
    card.className = "formula-dag__card";
    card.dataset.node = id;
    const stage = document.createElement("div");
    stage.className = "formula-dag__stage";
    const tints = document.createElementNS(SVGNS, "svg");
    tints.setAttribute("class", "formula-dag__tints");
    const tex = document.createElement("div");
    tex.className = "formula-dag__tex";
    const noteArrows = document.createElementNS(SVGNS, "svg");
    noteArrows.setAttribute("class", "formula-dag__note-arrows");
    stage.append(tints, tex, noteArrows);
    const labels = {};
    for (const [name, note] of Object.entries(getNotes())) {
      if (note.formula !== id) continue;
      const label = document.createElement("div");
      label.className = "formula-dag__note";
      label.dataset.annotation = name;
      label.innerHTML = noteHtml(katex, note.text);
      setColorVars(label, note.color);
      stage.appendChild(label);
      labels[name] = label;
    }
    const caption = document.createElement("div");
    caption.className = "formula-dag__label";
    caption.textContent = spec.label;
    card.append(stage, caption);
    card.addEventListener("mouseenter", () => isInteractive() && focus(id));
    card.addEventListener("mouseleave", () => isInteractive() && focus(null));
    card.addEventListener("click", (event) => {
      if (!isInteractive() || suppressClick || event.target.closest("[data-tangle-param], .formula-dag__note")) return;
      model.set("selected", model.get("selected") === id ? "" : id);
      model.save_changes();
    });
    cards[id] = card;
    parts[id] = { stage, tex, tints, noteArrows, labels, caption };
    return card;
  }

  // ---- rendering one formula ----------------------------------------------

  function showValue(name, spec) {
    return spec.display === "number" || editingName === name || (drag && drag.name === name);
  }

  // The number being dragged or typed into ("" when none).
  function activeParam() {
    return (drag && drag.name) || editingName || "";
  }

  // A computed formula shows its live value in place of its symbol (and of
  // every use) while a number it depends on is being changed.
  function revealed(spec) {
    const active = activeParam();
    return Boolean(spec && spec.has_fn && active && spec.inputs.includes(active));
  }

  function valueTex(name) {
    const shown = outputText(name);
    return shown === "—" ? String.raw`\text{—}` : shown;
  }

  // The LaTeX a card shows right now: \use{...} expanded to the producer's
  // symbol or live value, the output symbol likewise, then the numbers.
  function cardSource(spec) {
    const byName = formulasByName();
    const params = getParameters();
    const values = getValues();
    // An exponent right after a subscripted symbol (\use{vy}^2 with v_y)
    // moves inside it, so KaTeX stacks v_y^2 instead of raising the 2 over
    // the whole v_y.
    let source = spec.tex.replace(/\\use\{([^}]*)\}(\^(?:\{[^{}]*\}|[^{}\s\\]))?/g, (_, name, sup = "") => {
      const producer = byName[name];
      const absorb = sup && producer.symbol.includes("_") && !producer.symbol.includes("^");
      const content = revealed(producer) ? valueTex(name) : producer.symbol;
      if (absorb) return String.raw`\htmlData{fdag-use=${name}}{${content}${sup}}`;
      return String.raw`\htmlData{fdag-use=${name}}{${content}}` + sup;
    });
    const live = revealed(spec);
    if (spec.lhs) {
      // Keep a note that wraps the whole output on the value, so it still
      // points at something: \note{d1}{d_1} becomes \note{d1}{0.350}.
      let out = spec.lhs;
      if (live) out = spec.out_note ? String.raw`\note{${spec.out_note}}{${valueTex(spec.name)}}` : valueTex(spec.name);
      source = String.raw`\htmlData{fdag-out=${spec.name}}{${out}} =` + source;
    } else if (live) {
      // No output symbol to replace: close the formula with the value.
      source += String.raw` = \htmlData{fdag-value=${spec.name}}{${valueTex(spec.name)}}`;
    }
    return source.replace(/\\tangle\{([A-Za-z][A-Za-z0-9_-]*)\}/g, (_, name) => {
      const p = params[name];
      const content = showValue(name, p) ? formatValue(values[name], p.digits) : p.symbol;
      return String.raw`\htmlData{tangle-param=${name}}{${content}}`;
    });
  }

  // Re-render every card whose LaTeX changed; lay out again if any did.
  function renderAll() {
    let changed = false;
    for (const id of Object.keys(cards)) changed = renderCard(id) || changed;
    if (changed) relayoutSoon();
  }

  // Returns whether KaTeX re-rendered (unchanged LaTeX keeps its DOM).
  function renderCard(id) {
    const spec = formulasByName()[id];
    const { tex } = parts[id];
    const params = getParameters();
    const values = getValues();
    const producers = new Set((model.get("routes") || []).map((r) => r[0]));
    const source = cardSource(spec);
    const changed = source !== lastSource[id];
    if (changed) {
      lastSource[id] = source;
      try {
        katex.render(source, tex, {
          displayMode: true,
          throwOnError: true,
          macros: { "\\note": "\\htmlData{note=#1}{#2}" },
          trust: (context) => context.command === "\\htmlData",
          strict: (code) => (code === "htmlExtension" ? "ignore" : "warn"),
        });
        tex.classList.remove("formula-dag__tex--error");
        delete errors[id];
      } catch (error) {
        tex.textContent = spec.lhs ? `${spec.lhs} =${spec.tex}` : spec.tex;
        tex.classList.add("formula-dag__tex--error");
        errors[id] = `${id}: ${error instanceof Error ? error.message : error}`;
      }
      const message = Object.values(errors).join("\n");
      if (model.get("error") !== message) {
        model.set("error", message);
        model.save_changes();
      }
    }

    // Color this formula's output symbol (if anyone uses it), every use of
    // another formula's output, every number, and every noted part.
    const byName = formulasByName();
    const out = tex.querySelector(".katex-html [data-fdag-out]");
    if (out && producers.has(id)) setColorVars(out, spec.color);
    tex.querySelectorAll(".katex-html [data-fdag-use]").forEach((use) => {
      const producer = byName[use.dataset.fdagUse];
      if (producer) setColorVars(use, producer.color);
    });
    tex.querySelectorAll(".katex-html [data-tangle-param]").forEach((target) => {
      const name = target.dataset.tangleParam;
      const p = params[name];
      target.tabIndex = 0;
      target.setAttribute("role", "button");
      target.setAttribute(
        "aria-label",
        `${p.label}: ${formatValue(values[name], p.digits)}. Drag horizontally or press Enter to type.`,
      );
      setColorVars(target, p.color);
      target.classList.toggle("is-active", Boolean(drag && drag.name === name));
    });
    const notes = getNotes();
    tex.querySelectorAll(".katex-html [data-note]").forEach((term) => {
      const note = notes[term.dataset.note];
      if (!note) return;
      term.classList.add("formula-dag__note-term");
      term.tabIndex = 0;
      term.setAttribute("aria-label", note.text);
      setColorVars(term, note.color);
    });
    const valueNode = tex.querySelector(".katex-html [data-fdag-value]");
    if (valueNode) valueNode.title = (model.get("output_errors") || {})[id] || "";
    spaceNumbersAfterDigits(tex);
  }

  // A revealed number right after a digit reads as one number (2σ with
  // σ = 1.7 shows as "21.7", K·D as "1000.951"); give such a number (a
  // dragged one, or a live value standing in for a symbol) a small gap.
  function spaceNumbersAfterDigits(tex) {
    const html = tex.querySelector(".katex-html");
    if (!html) return;
    const walker = document.createTreeWalker(html, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    let previous = "";
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.textContent.trim();
      if (!text) continue;
      const param = node.parentElement.closest("[data-tangle-param], [data-fdag-use], [data-fdag-out]");
      if (param && !seen.has(param)) {
        seen.add(param);
        param.classList.toggle("formula-dag__param--gap", /[0-9.]$/.test(previous) && /^[0-9.]/.test(text));
      }
      previous = text;
    }
  }

  // ---- notes inside one card ------------------------------------------------

  function layoutNotes(id) {
    const { stage, tex, tints, noteArrows, labels } = parts[id];
    tints.replaceChildren();
    noteArrows.replaceChildren();
    const notes = getNotes();
    const names = Object.keys(labels);
    stage.style.padding = "";
    if (!names.length) return;

    const base = () => stage.getBoundingClientRect();
    const rel = (r, b = base()) => ({
      left: r.left - b.left,
      right: r.right - b.left,
      top: r.top - b.top,
      bottom: r.bottom - b.top,
      cx: r.left - b.left + (r.right - r.left) / 2,
      cy: r.top - b.top + (r.bottom - r.top) / 2,
    });
    const termOf = (name) => tex.querySelector(`.katex-html [data-note="${name}"]`);
    const termBox = (term) => {
      const html = tex.querySelector(".katex-html");
      const own = html ? glyphLeaves(term).map(inkRect) : [];
      return rel(union(own) || term.getBoundingClientRect());
    };

    // 1. Pick a side per note, as TangleLatex does: parts above the
    //    formula's middle go up, parts below go down, the rest balance.
    const texBox = rel(tex.getBoundingClientRect());
    // The formula's own width. The tex box stretches to the card, which a
    // wide caption can widen; measuring that would under-reserve room for
    // labels once left padding shifts the formula over.
    const html = tex.querySelector(".katex-html");
    const ink = html && union(glyphLeaves(html).map(inkRect));
    const formulaW = ink ? rel(ink).right - texBox.left : texBox.right - texBox.left;
    const items = [];
    //    A note on the output symbol (\note{why}{d_1} = ...) goes to the
    //    left instead: above it arrows come in, below it the stem leaves.
    const counts = { top: 0, bottom: 0 };
    const undecided = [];
    const out = tex.querySelector(".katex-html [data-fdag-out]");
    for (const name of names) {
      const term = termOf(name);
      // A live value can stand in for a noted part; hide its note meanwhile.
      labels[name].style.display = term ? "" : "none";
      if (!term) continue;
      const box = termBox(term);
      const item = {
        name,
        ...notes[name],
        label: labels[name],
        cx: box.cx - texBox.left,
        leftRel: box.left - texBox.left,
        cyRel: box.cy - texBox.top,
      };
      if (item.side === "auto" && out && out.contains(term)) item.side = "left";
      item.label.classList.toggle("formula-dag__note--left", item.side === "left");
      item.w = item.label.offsetWidth;
      item.h = item.label.offsetHeight;
      items.push(item);
      if (item.side === "auto") {
        const offset = box.cy - texBox.cy;
        if (offset < -4) item.side = "top";
        else if (offset > 4) item.side = "bottom";
        else undecided.push(item);
      }
      if (item.side !== "auto") counts[item.side] += 1;
    }
    // Undecided notes (terms on the formula's axis) take the side with fewer
    // DAG arrows crossing their label's span, then balance.
    const crossing = (item, side) =>
      ((blocks[id] || {})[side] || []).filter(
        (x) => x > item.cx - item.w / 2 - LANE_CLEARANCE && x < item.cx + item.w / 2 + LANE_CLEARANCE,
      ).length;
    for (const item of undecided) {
      const top = crossing(item, "top");
      const bottom = crossing(item, "bottom");
      if (top !== bottom) item.side = top < bottom ? "top" : "bottom";
      else item.side = counts.top <= counts.bottom ? "top" : "bottom";
      counts[item.side] += 1;
    }

    // 2. One row of labels per side, kept clear of the DAG arrows passing
    //    through it (x relative to the formula's left edge).
    const heights = {};
    let minX = 0;
    let maxX = formulaW;
    for (const side of ["top", "bottom"]) {
      const row = items.filter((item) => item.side === side).sort((a, b) => a.cx - b.cx);
      const sideBlocks = ((blocks[id] || {})[side] || []).map((x) => ({
        left: x - LANE_CLEARANCE,
        right: x + LANE_CLEARANCE,
      }));
      packRow(row, sideBlocks);
      heights[side] = row.length ? Math.max(...row.map((item) => item.h)) : 0;
      for (const item of row) {
        minX = Math.min(minX, item.x);
        maxX = Math.max(maxX, item.x + item.w);
      }
    }
    // Left-hand labels stack, centered on their terms' height.
    const lefts = items.filter((item) => item.side === "left");
    let needTop = 0;
    let needBottom = 0;
    if (lefts.length) {
      const stack = lefts.reduce((sum, item) => sum + item.h, 0) + NOTE_GAP / 2 * (lefts.length - 1);
      const cy = lefts.reduce((sum, item) => sum + item.cyRel, 0) / lefts.length;
      const edge = Math.min(...lefts.map((item) => item.leftRel)) - NOTE_SIDE_SPACE;
      let y = cy - stack / 2;
      for (const item of lefts) {
        item.x = edge - item.w;
        item.yRel = y;
        y += item.h + NOTE_GAP / 2;
        minX = Math.min(minX, item.x);
      }
      const texH = texBox.bottom - texBox.top;
      needTop = Math.max(0, -(cy - stack / 2)) + (cy - stack / 2 < 0 ? NOTE_PAD_Y : 0);
      needBottom = Math.max(0, cy + stack / 2 - texH) + (cy + stack / 2 > texH ? NOTE_PAD_Y : 0);
    }
    const band = (side) => (heights[side] ? NOTE_ARROW_SPACE + heights[side] + NOTE_PAD_Y : 0);
    // Labels wider than the formula widen the card instead of spilling out.
    stage.style.paddingTop = `${Math.max(band("top"), needTop)}px`;
    stage.style.paddingBottom = `${Math.max(band("bottom"), needBottom)}px`;
    stage.style.paddingLeft = `${-minX}px`;
    stage.style.paddingRight = `${maxX - formulaW}px`;

    // 3. Padding moved the formula: measure again and place the labels.
    const formula = rel(tex.getBoundingClientRect());
    for (const item of items) {
      const top =
        item.side === "left"
          ? formula.top + item.yRel
          : item.side === "top"
            ? formula.top - NOTE_ARROW_SPACE - item.h
            : formula.bottom + NOTE_ARROW_SPACE;
      item.label.style.left = `${formula.left + item.x}px`;
      item.label.style.top = `${top}px`;
    }

    // 4. A soft tint behind every noted part.
    for (const node of tex.querySelectorAll(".katex-html [data-note]")) {
      const note = notes[node.dataset.note];
      if (!note) continue;
      const box = termBox(node);
      const rect = document.createElementNS(SVGNS, "rect");
      rect.setAttribute("class", "formula-dag__tint");
      rect.dataset.annotation = node.dataset.note;
      rect.setAttribute("x", box.left - 3);
      rect.setAttribute("y", box.top - 3);
      rect.setAttribute("width", box.right - box.left + 6);
      rect.setAttribute("height", box.bottom - box.top + 6);
      rect.setAttribute("rx", 4);
      setColorVars(rect, note.color);
      tints.appendChild(rect);
    }

    // 5. A gentle S-curve from each label to its term (open chevron, so
    //    notes read differently from the DAG's filled data-flow arrows).
    for (const item of items) {
      const term = termBox(termOf(item.name));
      const label = rel(item.label.getBoundingClientRect());
      if (item.side === "left") {
        noteArrows.appendChild(sideNoteArrow(item, label, term));
        continue;
      }
      const top = item.side === "top";
      const fromX = Math.max(label.left + 8, Math.min(term.cx, label.right - 8));
      const from = { x: fromX, y: top ? label.bottom + NOTE_CLEARANCE : label.top - NOTE_CLEARANCE };
      const to = { x: term.cx, y: top ? term.top - NOTE_CLEARANCE - 3 : term.bottom + NOTE_CLEARANCE + 3 };
      const midY = (from.y + to.y) / 2;
      const dir = Math.sign(to.y - from.y) || 1;
      const backY = to.y - dir * NOTE_HEAD_LEN;
      const group = document.createElementNS(SVGNS, "g");
      group.setAttribute("class", "formula-dag__note-arrow");
      group.dataset.annotation = item.name;
      setColorVars(group, item.color);
      for (const d of [
        `M ${from.x} ${from.y} C ${from.x} ${midY} ${to.x} ${midY} ${to.x} ${to.y}`,
        `M ${to.x - NOTE_HEAD_HALF} ${backY} L ${to.x} ${to.y} L ${to.x + NOTE_HEAD_HALF} ${backY}`,
      ]) {
        const path = document.createElementNS(SVGNS, "path");
        path.setAttribute("d", d);
        group.appendChild(path);
      }
      noteArrows.appendChild(group);
    }
  }

  // A left-hand note points straight right into the output symbol.
  function sideNoteArrow(item, label, term) {
    const from = { x: label.right + NOTE_CLEARANCE, y: (label.top + label.bottom) / 2 };
    const to = { x: term.left - NOTE_CLEARANCE - 2, y: term.cy };
    const midX = (from.x + to.x) / 2;
    const backX = to.x - NOTE_HEAD_LEN;
    const group = document.createElementNS(SVGNS, "g");
    group.setAttribute("class", "formula-dag__note-arrow");
    group.dataset.annotation = item.name;
    setColorVars(group, item.color);
    for (const d of [
      `M ${from.x} ${from.y} C ${midX} ${from.y} ${midX} ${to.y} ${to.x} ${to.y}`,
      `M ${backX} ${to.y - NOTE_HEAD_HALF} L ${to.x} ${to.y} L ${backX} ${to.y + NOTE_HEAD_HALF}`,
    ]) {
      const path = document.createElementNS(SVGNS, "path");
      path.setAttribute("d", d);
      group.appendChild(path);
    }
    return group;
  }

  // Notes move formulas and arrows move notes: lay notes out around the last
  // known arrow columns, draw the arrows, and once more if the columns moved.
  function relayout() {
    if (disposed || !board) return;
    const before = JSON.stringify(blocks);
    Object.keys(parts).forEach(layoutNotes);
    draw();
    if (JSON.stringify(blocks) !== before) {
      Object.keys(parts).forEach(layoutNotes);
      draw();
    }
    applyHover();
  }

  function relayoutSoon() {
    if (relayoutQueued) return;
    relayoutQueued = true;
    requestAnimationFrame(() => {
      relayoutQueued = false;
      relayout();
    });
  }

  // ---- DAG arrows -------------------------------------------------------------

  function draw() {
    if (disposed || !board) return;
    svg.replaceChildren();
    edgeEls = [];
    const base = board.getBoundingClientRect();
    const rel = (r) => ({
      left: r.left - base.left,
      right: r.right - base.left,
      top: r.top - base.top,
      bottom: r.bottom - base.top,
    });
    const box = (node) => rel(node.getBoundingClientRect());
    const byName = formulasByName();
    const rowBoxes = rowEls.map(box);
    const producers = new Set((model.get("routes") || []).map((r) => r[0]));
    const texHtml = (id) => parts[id].tex.querySelector(".katex-html");

    // Per card: the ink box of every glyph, and of the formula as a whole.
    const glyphs = {};
    const formulaInk = {};
    const texLeft = {};
    for (const id of Object.keys(cards)) {
      const html = texHtml(id);
      glyphs[id] = html ? glyphLeaves(html).map((g) => ({ el: g, ...rel(inkRect(g)) })) : [];
      formulaInk[id] = union(glyphs[id]) || box(cards[id]);
      texLeft[id] = box(parts[id].tex).left;
    }
    const inkOf = (id, node) => union(glyphs[id].filter((g) => node.contains(g.el))) || box(node);

    // Outgoing arrows share one stem that drops from under the output symbol.
    const stems = {};
    for (const id of Object.keys(cards)) {
      const out = texHtml(id)?.querySelector("[data-fdag-out]");
      const sym = out ? inkOf(id, out) : formulaInk[id];
      stems[id] = { x: (sym.left + sym.right) / 2, top: sym.bottom + LAND_GAP, width: sym.right - sym.left };
    }
    // A caption sits right of its formula's stem, never across it.
    for (const id of producers) {
      if (!stems[id]) continue;
      const card = box(cards[id]);
      const pad = parseFloat(getComputedStyle(cards[id]).paddingLeft) || 0;
      const margin = Math.max(0, Math.round(stems[id].x - card.left - pad + 8));
      const caption = parts[id].caption;
      if (caption.style.marginLeft !== `${margin}px`) caption.style.marginLeft = `${margin}px`;
    }
    const newBlocks = {};
    const block = (id, side, x) => {
      const b = (newBlocks[id] ||= { top: [], bottom: [] });
      b[side].push(Math.round(x - texLeft[id]));
    };
    for (const id of producers) if (stems[id]) block(id, "bottom", stems[id].x);

    // 1. Work out every arrow's columns: the x it holds in each row it passes.
    const arrows = [];
    for (const route of model.get("routes") || []) {
      const src = route[0];
      const dst = route[route.length - 1];
      if (!cards[src] || !cards[dst] || !(src in rowOf) || !(dst in rowOf)) continue;
      const ink = formulaInk[dst];
      const uses = [...(texHtml(dst)?.querySelectorAll(`[data-fdag-use="${src}"]`) || [])];
      for (const use of uses.length ? uses : [null]) {
        let landing;
        if (!use) {
          const x = (ink.left + ink.right) / 2;
          landing = { side: "top", x, tip: { x, y: ink.top - LAND_GAP } };
        } else {
          const sym = inkOf(dst, use);
          const cx = (sym.left + sym.right) / 2;
          const cy = (sym.top + sym.bottom) / 2;
          // Avoid the target's other glyphs and, if it feeds anything itself,
          // the stem dropping out of its own output symbol.
          const others = glyphs[dst].filter((g) => !use.contains(g.el));
          if (producers.has(dst)) {
            const st = stems[dst];
            others.push({ left: st.x - st.width / 2, right: st.x + st.width / 2, top: st.top, bottom: box(cards[dst]).bottom });
          }
          const side = landingSide(sym, others, stems[src].x);
          if (side === "top") {
            landing = { side, x: cx, tip: { x: cx, y: sym.top - LAND_GAP } };
          } else if (side === "right") {
            landing = { side, x: ink.right + SIDE_GAP, tip: { x: sym.right + LAND_GAP, y: cy } };
          } else {
            landing = { side, x: ink.left - SIDE_GAP, tip: { x: sym.left - LAND_GAP, y: cy } };
          }
        }
        block(dst, "top", landing.x);
        // A long edge threads one reserved lane per row it skips. Lanes sit at
        // different x in each row, so straighten them into a single vertical
        // when that line clears every formula in those rows.
        const waypoints = route.slice(1, -1);
        let laneXs = waypoints.map((wp) => {
          const lane = box(lanes[wp]);
          return (lane.left + lane.right) / 2;
        });
        if (laneXs.length > 1) {
          const passed = waypoints
            .flatMap((wp) => [...rowEls[rowOf[wp]].children])
            .filter((n) => n.classList.contains("formula-dag__card"))
            .map(box);
          const clear = (x) => passed.every((b) => x < b.left - 6 || x > b.right + 6);
          const straight = [Math.max(...laneXs), Math.min(...laneXs)].find(clear);
          if (straight !== undefined) laneXs = laneXs.map(() => straight);
        }
        const xs = [stems[src].x, ...laneXs, landing.x];
        arrows.push({ src, dst, row: rowOf[src], xs, landing });
      }
    }
    blocks = newBlocks;

    // 2. Each gap between two rows gets one horizontal track per producer
    //    that jogs sideways there; its arrows share it like a bus. Stack the
    //    tracks in the order with the fewest crossings.
    const segs = {}; // gap -> {src: [{from, to}]}
    for (const a of arrows) {
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1 || Math.abs(a.xs[k + 1] - x) < 1) return;
        const bySrc = (segs[a.row + k] ||= {});
        (bySrc[a.src] ||= []).push({ from: x, to: a.xs[k + 1] });
      });
    }
    const tracks = {}; // gap -> [src, ...] top to bottom
    for (const [g, bySrc] of Object.entries(segs)) {
      const seed = Object.keys(bySrc).sort((p, q) => stems[p].x - stems[q].x);
      let best = seed;
      if (seed.length <= 6) {
        let bestCost = trackCrossings(seed, bySrc);
        for (const order of permutations(seed)) {
          if (bestCost === 0) break;
          const cost = trackCrossings(order, bySrc);
          if (cost < bestCost) {
            best = order;
            bestCost = cost;
          }
        }
      }
      tracks[g] = best;
    }
    const trackY = (g, src) => {
      const top = rowBoxes[g].bottom;
      const h = rowBoxes[g + 1].top - top;
      const list = tracks[g];
      return top + (h * (list.indexOf(src) + 1)) / (list.length + 1);
    };

    // 3. Draw: down, rounded jog along the track, down again; finally into
    //    the symbol from above or, if covered, from the side.
    for (const a of arrows) {
      const { tip, side } = a.landing;
      let d = `M ${a.xs[0]} ${stems[a.src].top}`;
      a.xs.forEach((x, k) => {
        if (k === a.xs.length - 1) return;
        const next = a.xs[k + 1];
        if (Math.abs(next - x) < 1) return;
        const ty = trackY(a.row + k, a.src);
        const s = Math.sign(next - x);
        const r = Math.min(CORNER, Math.abs(next - x) / 2);
        d += ` L ${x} ${ty - r} Q ${x} ${ty}, ${x + s * r} ${ty}`;
        d += ` L ${next - s * r} ${ty} Q ${next} ${ty}, ${next} ${ty + r}`;
      });
      const last = a.xs[a.xs.length - 1];
      let dir;
      if (side === "top") {
        dir = { x: 0, y: 1 };
      } else {
        const s = side === "right" ? -1 : 1; // direction of travel into the symbol
        d += ` L ${last} ${tip.y - CORNER} Q ${last} ${tip.y}, ${last + s * CORNER} ${tip.y}`;
        dir = { x: s, y: 0 };
      }
      // Stop the line at the arrowhead's base so it doesn't poke through.
      d += ` L ${tip.x - dir.x * HEAD_LEN * 0.8} ${tip.y - dir.y * HEAD_LEN * 0.8}`;

      const color = byName[a.src].color;
      const path = document.createElementNS(SVGNS, "path");
      path.setAttribute("d", d);
      path.setAttribute("class", "formula-dag__edge");
      setColorVars(path, color);
      const head = document.createElementNS(SVGNS, "path");
      const bx = tip.x - dir.x * HEAD_LEN;
      const by = tip.y - dir.y * HEAD_LEN;
      head.setAttribute(
        "d",
        `M ${tip.x} ${tip.y} L ${bx - dir.y * HEAD_HALF} ${by + dir.x * HEAD_HALF} ` +
          `L ${bx + dir.y * HEAD_HALF} ${by - dir.x * HEAD_HALF} Z`,
      );
      head.setAttribute("class", "formula-dag__head");
      setColorVars(head, color);
      svg.append(path, head);
      edgeEls.push({ src: a.src, dst: a.dst, els: [path, head] });
    }
    focus(focused);
  }

  // ---- hover & selection ------------------------------------------------------

  // Hovering a card keeps it, everything upstream, and everything downstream;
  // the rest dims.
  let focused = null;
  function focus(name) {
    focused = name;
    if (!name) {
      Object.values(cards).forEach((c) => c.classList.remove("is-dim"));
      edgeEls.forEach((e) => e.els.forEach((p) => p.classList.remove("is-dim")));
      return;
    }
    const down = {};
    const up = {};
    for (const route of model.get("routes") || []) {
      const s = route[0];
      const t = route[route.length - 1];
      (down[s] ||= []).push(t);
      (up[t] ||= []).push(s);
    }
    const ups = reach(name, up);
    const downs = reach(name, down);
    ups.add(name);
    downs.add(name);
    for (const [id, card] of Object.entries(cards)) {
      card.classList.toggle("is-dim", !ups.has(id) && !downs.has(id));
    }
    for (const e of edgeEls) {
      const keep = (ups.has(e.src) && ups.has(e.dst)) || (downs.has(e.src) && downs.has(e.dst));
      e.els.forEach((p) => p.classList.toggle("is-dim", !keep));
    }
  }

  function showSelected() {
    const selected = model.get("selected");
    for (const [id, card] of Object.entries(cards)) {
      card.classList.toggle("is-selected", id === selected);
    }
  }

  // The note that explains a parameter: the one wrapping exactly it.
  function noteForParam(param) {
    const match = Object.entries(getNotes()).find(([, note]) => note.param === param);
    return match ? match[0] : "";
  }

  // The highlighted note (the dragged parameter's wins over the hovered one)
  // lifts; every other note fades.
  function applyHover() {
    if (!board) return;
    const name = drag ? noteForParam(drag.name) : model.get("hovered");
    const active = Boolean(name) && name in getNotes();
    root.classList.toggle("has-note-hover", active);
    for (const node of board.querySelectorAll("[data-annotation]")) {
      node.classList.toggle("is-hovered", active && node.dataset.annotation === name);
    }
    for (const node of board.querySelectorAll(".katex-html [data-note]")) {
      node.classList.toggle("is-hovered", active && node.dataset.note === name);
    }
  }

  function setHovered(name) {
    if (!isInteractive()) return;
    if (model.get("hovered") !== name) {
      model.set("hovered", name);
      model.save_changes();
    }
    applyHover();
  }

  // Light up every occurrence of one number (in formulas and the legend).
  function applyLinked() {
    const name = drag ? drag.name : linked;
    for (const node of root.querySelectorAll("[data-tangle-param]")) {
      node.classList.toggle("is-linked", Boolean(name) && node.dataset.tangleParam === name);
    }
    // An output chip lights up its formula's output and every use of it.
    const out = linkedOutput;
    for (const node of root.querySelectorAll(".katex-html [data-fdag-out], .katex-html [data-fdag-use]")) {
      const which = node.dataset.fdagOut || node.dataset.fdagUse;
      node.classList.toggle("is-linked", Boolean(out) && which === out);
    }
    for (const [name, { chip }] of Object.entries(outputChips)) {
      chip.classList.toggle("is-linked", name === out);
    }
  }

  function handleHover(event) {
    if (!isInteractive()) return;
    const over = event.target.closest("[data-tangle-param]");
    const next = over ? over.dataset.tangleParam : "";
    const outChip = event.target.closest("[data-fdag-link]");
    const nextOutput = outChip ? outChip.dataset.fdagLink : "";
    if (next !== linked || nextOutput !== linkedOutput) {
      linked = next;
      linkedOutput = nextOutput;
      applyLinked();
    }
    const label = event.target.closest(".formula-dag__note");
    if (label) return setHovered(label.dataset.annotation);
    const param = event.target.closest("[data-tangle-param]");
    const paramNote = param ? noteForParam(param.dataset.tangleParam) : "";
    if (paramNote) return setHovered(paramNote);
    const term = event.target.closest("[data-note]");
    setHovered(term ? term.dataset.note : "");
  }

  // ---- dragging & editing numbers -------------------------------------------

  function rerender() {
    renderAll();
    renderLegend();
    applyLinked();
  }

  // Where a number was grabbed: a formula card and which occurrence in it,
  // or the legend (card null). Rendering replaces the elements, so find the
  // grabbed one again from this.
  function whereOf(target) {
    const name = target.dataset.tangleParam;
    const card = target.closest(".formula-dag__card")?.dataset.node ?? null;
    if (!card) return { card: null, occurrence: 0 };
    const all = [...parts[card].tex.querySelectorAll(`[data-tangle-param="${name}"]`)];
    return { card, occurrence: all.indexOf(target) };
  }

  function findTarget(name, where) {
    if (!where.card) return legend[name]?.value;
    const all = parts[where.card].tex.querySelectorAll(`.katex-html [data-tangle-param="${name}"]`);
    return all[Math.max(0, where.occurrence)] || all[0];
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

  // Ends a drag or an edit: committed_values catches up with values.
  function commit() {
    model.set("committed_values", { ...getValues() });
    model.set("dragging", false);
    flushSave();
  }

  function updateValue(name, value, { flush = false } = {}) {
    localValuesUpdate = true;
    model.set("values", { ...getValues(), [name]: value });
    rerender();
    if (flush) commit();
    else scheduleSave();
  }

  function startDrag(event) {
    if (!isInteractive()) return;
    const target = event.target.closest("[data-tangle-param]");
    if (!target || (event.pointerType === "mouse" && event.button !== 0)) return;
    event.preventDefault();
    const name = target.dataset.tangleParam;
    closeEditor(false);
    drag = {
      name,
      where: whereOf(target),
      pointerId: event.pointerId,
      startX: event.clientX,
      startValue: getValues()[name],
      spec: getParameters()[name],
      moved: false,
    };
    root.classList.add("is-dragging");
    rerender();
  }

  function moveDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const deltaX = event.clientX - drag.startX;
    if (!drag.moved && Math.abs(deltaX) >= 3) {
      drag.moved = true;
      // Tell Python first, so it keeps committed_values where they were.
      model.set("dragging", true);
      flushSave();
    }
    if (!drag.moved) return;
    event.preventDefault();
    const steps = Math.trunc(deltaX / drag.spec.pixels_per_step);
    const next = roundForStep(
      clamp(drag.startValue + steps * drag.spec.step, drag.spec.min_value, drag.spec.max_value),
      drag.spec.step,
    );
    if (getValues()[drag.name] !== next) updateValue(drag.name, next);
  }

  function endDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const finished = drag;
    drag = null;
    root.classList.remove("is-dragging");
    // The click that follows a drag must not toggle the card's selection.
    suppressClick = true;
    setTimeout(() => (suppressClick = false), 0);
    if (finished.moved) {
      rerender();
      commit();
      return;
    }
    openEditor(finished.name, finished.where);
  }

  function cancelDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const finished = drag;
    drag = null;
    root.classList.remove("is-dragging");
    rerender();
    if (finished.moved) commit();
  }

  function openEditor(name, where) {
    closeEditor(false);
    const spec = getParameters()[name];
    editingName = name;
    renderAll();
    relayout();
    const target = findTarget(name, where);
    if (!target) return;
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.className = "formula-dag__editor";
    input.value = formatValue(getValues()[name], spec.digits);
    input.setAttribute("aria-label", `Set ${spec.label}`);
    setColorVars(input, spec.color);
    const t = target.getBoundingClientRect();
    const b = root.getBoundingClientRect();
    input.style.left = `${t.left + t.width / 2 - b.left}px`;
    input.style.top = `${t.bottom - b.top + 8}px`;
    root.appendChild(input);
    editor = { input, name, spec };
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        closeEditor(true);
      } else if (event.key === "Escape") {
        event.preventDefault();
        closeEditor(false);
      }
    });
    input.addEventListener("blur", () => closeEditor(false));
    input.focus();
    input.select();
  }

  function closeEditor(save) {
    if (!editor) return;
    const current = editor;
    if (save) {
      const parsed = Number(current.input.value);
      if (current.input.value.trim() === "" || !Number.isFinite(parsed)) {
        current.input.classList.add("is-invalid");
        current.input.focus();
        current.input.select();
        return;
      }
    }
    editor = null;
    editingName = null;
    current.input.remove();
    if (save) updateValue(current.name, snap(Number(current.input.value), current.spec), { flush: true });
    else rerender();
  }

  function handleKeydown(event) {
    if (!isInteractive()) return;
    const target = event.target.closest("[data-tangle-param]");
    if (!target || (event.key !== "Enter" && event.key !== " ")) return;
    event.preventDefault();
    openEditor(target.dataset.tangleParam, whereOf(target));
  }

  function handleReset() {
    if (!isInteractive()) return;
    closeEditor(false);
    drag = null;
    root.classList.remove("is-dragging");
    localValuesUpdate = true;
    const initial = Object.fromEntries(Object.entries(getParameters()).map(([n, p]) => [n, p.value]));
    model.set("values", initial);
    renderAll();
    renderLegend();
    commit();
  }

  function handleValuesChange() {
    if (localValuesUpdate) {
      localValuesUpdate = false;
      return;
    }
    renderAll();
    renderLegend();
  }

  // ---- wiring -----------------------------------------------------------------

  const observer = new ResizeObserver(relayoutSoon);
  observer.observe(root);
  document.fonts?.ready.then(relayoutSoon);
  const timers = [setTimeout(relayout, 80), setTimeout(relayout, 400)];
  // Follow notebook theme toggles (a class/attribute flip on some ancestor)
  // and OS theme changes.
  const themeObserver = new MutationObserver(setTheme);
  themeObserver.observe(document.documentElement, {
    attributes: true,
    subtree: true,
    attributeFilter: ["class", "data-theme", "data-color-mode", "data-jp-theme-light"],
  });
  const colorScheme = window.matchMedia?.("(prefers-color-scheme: dark)");
  colorScheme?.addEventListener("change", setTheme);

  const onHoverEnd = () => {
    linked = "";
    linkedOutput = "";
    applyLinked();
    setHovered("");
  };
  root.addEventListener("pointerover", handleHover);
  root.addEventListener("pointerleave", onHoverEnd);
  root.addEventListener("focusin", handleHover);
  root.addEventListener("pointerdown", startDrag);
  root.addEventListener("keydown", handleKeydown);
  root.addEventListener("dragstart", (event) => event.preventDefault());
  document.addEventListener("pointermove", moveDrag);
  document.addEventListener("pointerup", endDrag);
  document.addEventListener("pointercancel", cancelDrag);

  const rebuildOn = ["formulas", "layers", "routes", "parameters", "notes", "legend"];
  rebuildOn.forEach((name) => model.on(`change:${name}`, build));
  model.on("change:values", handleValuesChange);
  model.on("change:outputs", renderOutputs);
  model.on("change:output_errors", renderOutputs);
  model.on("change:hovered", applyHover);
  model.on("change:theme", setTheme);
  model.on("change:interactive", applyInteractive);
  model.on("change:selected", showSelected);
  build();

  return () => {
    disposed = true;
    clearTimeout(saveTimer);
    closeEditor(false);
    observer.disconnect();
    themeObserver.disconnect();
    colorScheme?.removeEventListener("change", setTheme);
    timers.forEach(clearTimeout);
    document.removeEventListener("pointermove", moveDrag);
    document.removeEventListener("pointerup", endDrag);
    document.removeEventListener("pointercancel", cancelDrag);
    rebuildOn.forEach((name) => model.off(`change:${name}`, build));
    model.off("change:values", handleValuesChange);
    model.off("change:outputs", renderOutputs);
    model.off("change:output_errors", renderOutputs);
    model.off("change:hovered", applyHover);
    model.off("change:theme", setTheme);
    model.off("change:interactive", applyInteractive);
    model.off("change:selected", showSelected);
  };
}

export default { render };
