/** @typedef {import("@anywidget/types").AnyModel} AnyModel */
/** @typedef {{render: (tex: string, el: HTMLElement, opts?: {throwOnError?: boolean}) => void}} KatexRenderer */

// KaTeX import semantics follow `latex-tangle.js`
const KATEX_VERSION = "0.17.0";
const KATEX_MODULE_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.mjs`;
const KATEX_CSS_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css`;

/** @type {Promise<any> | null} */
let katexPromise = null;

/*
 * Lazy singleton cache:
 * The first widget that sucessfully imports KaTeX sets the module-level variable `katexPromise`.
 * All subsequent calls to `loadKatex` return that same promise without re-importing KaTeX.
 */
function loadKatex() {
  if (!katexPromise) katexPromise = import(KATEX_MODULE_URL);
  return katexPromise;
}

function ensureKatexCss() {
  if (document.querySelector('link[data-scientific-number-katex="true"]'))
    return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = KATEX_CSS_URL;
  link.dataset.scientificNumberKatex = "true";
  document.head.appendChild(link);
}

/**
 * Round a number to a given number of decimal places using banker's rounding
 * (via Number.EPSILON guard).
 * @param {number} n
 * @param {number} decimals
 * @returns {number}
 */
function roundTo(n, decimals) {
  const f = Math.pow(10, decimals);
  return Math.round((n + Number.EPSILON) * f) / f;
}

/**
 * Decimal places needed to represent a step value cleanly.
 * Iteratively finds how many digits after the decimal are required before
 * multiplying by 10^d yields an integer (within FP tolerance). Capped at 10
 * to avoid runaway iteration on non-terminating fractions like 1/3.
 * @param {number} step
 * @returns {number}
 */
function decimalsForStep(step) {
  if (step >= 1) return 0;
  let d = Math.max(0, -Math.floor(Math.log10(step)));
  while (
    Math.abs(step * Math.pow(10, d) - Math.round(step * Math.pow(10, d))) >
      1e-9 &&
    d < 10
  ) {
    d++;
  }
  return d;
}

/**
 * Significant digits of a value relative to the step resolution.
 * @param {number} value
 * @param {number} step
 * @returns {number}
 */
function sigDigitsFromStep(value, step) {
  if (value === 0) return 1;
  return (
    Math.floor(Math.log10(Math.abs(value))) - Math.floor(Math.log10(step)) + 1
  );
}

/**
 * Floor of log10, with guard against near-integer rounding errors
 * (e.g. log10(1000) = 2.999… or 3.000…).
 * @param {number} abs
 * @returns {number}
 */
function safeLog10Floor(abs) {
  const raw = Math.log10(abs);
  const rounded = Math.round(raw);
  if (Math.abs(raw - rounded) < 1e-10) return rounded;
  return Math.floor(raw);
}

/**
 * Format a value as a fixed-point decimal string using the step's precision.
 * `Math.round(value / step) * step` is a no-op here — snapping happens on
 * the Python side — but kept as a safety net against un-snapped values.
 * @param {number} value
 * @param {number} step
 * @returns {string}
 */
function toFixedStep(value, step) {
  const d = decimalsForStep(step);
  const snapped = roundTo(Math.round(value / step) * step, d);
  return snapped.toFixed(d);
}

/**
 * Format a value in scientific notation with a given number of significant
 * digits.
 * @param {number} value
 * @param {number} sig
 * @returns {string}
 */
function toSciSig(value, sig) {
  if (value === 0) return "0e+0";
  if (sig <= 0) throw new Error("sig must be > 0");
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  let e = safeLog10Floor(abs);
  let m = abs / Math.pow(10, e);
  const decimals = sig - 1;
  m = roundTo(m, decimals);
  if (m >= 10) {
    m /= 10;
    e += 1;
  }
  const mantStr = m.toFixed(decimals);
  const expStr = (e >= 0 ? "+" : "-") + String(Math.abs(e)).padStart(1, "0");
  return `${sign}${mantStr}e${expStr}`;
}

/**
 * Formats a value in scientific notation with a given number of significant digits,
 * removing trailing zeros.
 * @param {number} value
 * @param {number} sig
 * @returns {string}
 */
function toSciSigShort(value, sig) {
  if (value === 0) return "0e+0";
  const [mant, exp] = toSciSig(value, sig).split("e");
  const stripped = mant.includes(".")
    ? mant.replace(/0+$/, "").replace(/\.$/, "")
    : mant;
  return `${stripped}e${exp}`;
}

/**
 * Format a value in scientific notation with significant digits derived from
 * the step resolution.
 * @param {number} value
 * @param {number} step
 * @returns {string}
 */
function toSciStep(value, step) {
  if (value === 0) return "0e+0";
  const sig = Math.max(1, sigDigitsFromStep(value, step));
  return toSciSig(value, sig);
}

/**
 * @param {{ model: AnyModel, el: HTMLElement }} context
 */
async function render({ model, el }) {
  ensureKatexCss();

  /** @type {KatexRenderer | null} */
  let katex = null;

  try {
    const module = await loadKatex();
    katex = module.default || module;
  } catch {
    // No KaTeX, no problem: every branch below falls back to plain text.
  }

  // DOM structure:
  //
  //   el (anywidget root; display: inline-flex)
  //   └── div.scientific-number                  horizontal flex row: [label | box]
  //       ├── span.scientific-number-label       KaTeX/plain label, left of the box
  //       └── div.scientific-number-box          bordered flex row [input | scale]
  //           ├── input.scientific-number-input  editable text field; accepts
  //           │                                  decimal or scientific notation
  //           └── span.scientific-number-scale   read-only right panel; holds the
  //                                              scale_label and unit_label spans,
  //                                              each rendered by renderScale

  const root = document.createElement("div");
  root.className = "scientific-number";

  const labelEl = document.createElement("span");
  labelEl.className = "scientific-number-label";

  const box = document.createElement("div");
  box.className = "scientific-number-box";

  const input = document.createElement("input");
  input.type = "text";
  input.inputMode = "decimal";
  input.className = "scientific-number-input";

  const scaleEl = document.createElement("span");
  scaleEl.className = "scientific-number-scale";

  box.append(input, scaleEl);
  root.append(labelEl, box);
  el.style.display = "inline-flex";
  el.appendChild(root);

  function renderInline() {
    const inline = model.get("inline_mode");
    root.classList.toggle("scientific-number-inline", inline);
    el.style.verticalAlign = inline ? "0.35em" : "";
  }

  /**
   * Render a string into a DOM element.
   * Strings wrapped in $...$ are rendered as KaTeX (if available);
   * everything else is set as plain text. KaTeX errors fall back
   * to plain text.
   * @param {HTMLElement} target
   * @param {string} source
   */
  function renderLatex(target, source) {
    target.innerHTML = "";
    if (!source) return;
    const isLatex =
      source.startsWith("$") && source.endsWith("$") && source.length > 1;
    if (isLatex && katex) {
      try {
        katex.render(source.slice(1, -1), target, { throwOnError: false });
        return;
      } catch {
        // fall through to plain text
      }
    }
    target.textContent = source;
  }

  function renderLabel() {
    renderLatex(labelEl, model.get("label"));
  }

  function renderScale() {
    const parts = [model.get("scale_label"), model.get("unit_label")].filter(
      Boolean,
    );
    scaleEl.innerHTML = "";
    parts.forEach((part, i) => {
      const span = document.createElement("span");
      if (i > 0) span.style.marginLeft = "0.4em";
      renderLatex(span, part);
      scaleEl.appendChild(span);
    });
  }

  function renderWidth() {
    root.style.width = model.get("width") + "px";
  }

  /**
   * Format a raw value for display using the step's precision.
   * Dispatches to toFixedStep or toSciStep based on the notation trait.
   * Without a step there is no precision signal, so fall back to formatting
   * assuming 12 significant digits.
   * @param {number} value
   * @returns {string}
   */
  function format(value) {
    const step = model.get("step");
    const notation = model.get("notation");
    if (step && Number.isFinite(step)) {
      if (notation === "scientific") return toSciStep(value, step);
      return toFixedStep(value, step);
    } else {
      if (notation === "scientific") return toSciSigShort(value, 12);
      return String(value.toPrecision(12));
    }
  }

  // The initial raw_value is the "default": it renders faintly in the input so
  // the user can see the starting number without confusing it for their own
  // input. Typing anything (or Python moving value) lifts the dimming. The
  // default is captured from the first finite value we see, in case the model
  // state arrives after render.
  /** @type {number?} */
  let defaultRaw = null;
  let editing = false;

  /**
   * Store the default value.
   * @param {number} raw
   */
  function noteDefault(raw) {
    if (defaultRaw === null && Number.isFinite(raw)) defaultRaw = raw;
  }

  /**
   * While
   * @param {Number} rawOverride - TODO:
   * */
  function paintInput(rawOverride) {
    noteDefault(rawOverride);
    if (Number.isFinite(rawOverride)) {
      // While the user is editing, leave the text alone: repainting from the
      // model on every keystroke would reformat (and truncate trailing zeros
      // past the decimal point) under their cursor. Blur applies the format.
      if (!editing && input.value !== format(rawOverride)) {
        input.value = format(rawOverride);
      }
      input.classList.toggle("is-default", rawOverride === defaultRaw);
    }
  }

  input.addEventListener("input", () => {
    const parsed = Number(input.value);
    if (Number.isFinite(parsed) && parsed !== model.get("raw_value")) {
      model.set("raw_value", parsed);
      model.save_changes();
    }
  });

  input.addEventListener("focus", () => {
    // Let other functions know that you are currently still editing the value.
    editing = true;
  });

  /**
   * Apply formatting and rounding/snapping logic to the input.
   */
  function commit() {
    editing = false;
    const raw = model.get("raw_value");
    if (Number.isFinite(raw) && input.value !== format(raw)) {
      input.value = format(raw);
    }
  }

  input.addEventListener("blur", commit);

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      commit();
      input.blur();
    }
  });

  model.on("change:raw_value", () => {
    const raw_value = model.get("raw_value");
    paintInput(raw_value);
  });

  model.on("change:value", () => {
    const scaled = model.get("value");
    const factor = model.get("scale") || 1;
    if (Number.isFinite(scaled)) paintInput(scaled / factor);
  });

  model.on("change:label", renderLabel);
  model.on("change:scale_label", renderScale);
  model.on("change:unit_label", renderScale);
  model.on("change:width", renderWidth);
  model.on("change:inline_mode", renderInline);
  model.on("change:notation", paintInput);

  renderLabel();
  renderScale();
  renderWidth();
  renderInline();
  paintInput(model.get("raw_value") || 0);

  return () => {};
}

export default { render };
