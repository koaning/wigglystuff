// TangleFunction: render a Python call expression whose arguments are editable.
// Numbers drag-scrub, Literal/Enum/bool choices click-cycle, strings click-edit.

function clampSpec(value, spec) {
  // Bounds are optional; a null min/max means "unbounded on that side".
  let result = value;
  if (spec.min_value != null) result = Math.max(spec.min_value, result);
  if (spec.max_value != null) result = Math.min(spec.max_value, result);
  return result;
}

function roundForStep(value, step) {
  const precision = Math.max(0, (String(step).split(".")[1] || "").length);
  return Number(value.toFixed(precision + 2));
}

function snap(value, spec) {
  const origin = spec.min_value != null ? spec.min_value : 0;
  const snapped = origin + Math.round((value - origin) / spec.step) * spec.step;
  return clampSpec(roundForStep(snapped, spec.step), spec);
}

function formatNumber(value, spec) {
  if (spec.is_int) return String(Math.round(value));
  const safe = Math.abs(value) < 10 ** (-(spec.digits + 1)) ? 0 : value;
  return safe.toFixed(spec.digits);
}

function quoteString(value) {
  return `'${String(value).replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
}

function sameValue(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function render({ model, el }) {
  const root = document.createElement("div");
  const line = document.createElement("div");
  line.className = "tangle-fn__line";
  root.appendChild(line);
  el.replaceChildren(root);

  const nodes = new Map(); // name -> { el, spec, kind, index }
  let drag = null;
  let editor = null;
  let localUpdate = false;
  let saveTimer = null;
  let disposed = false;

  function applyTheme() {
    root.className = `tangle-fn tangle-fn--theme-${model.get("theme")}`;
    root.style.maxWidth = `${model.get("width")}px`;
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

  function setValue(name, value, { flush = false } = {}) {
    localUpdate = true;
    model.set("values", { ...(model.get("values") || {}), [name]: value });
    if (flush) flushSave();
    else scheduleSave();
  }

  function displayText(node) {
    const values = model.get("values") || {};
    const value = values[node.name];
    if (node.kind === "number") return formatNumber(value, node.spec);
    if (node.kind === "string") return quoteString(value);
    // choice
    const options = node.spec.options;
    let index = options.findIndex((option) => sameValue(option, value));
    if (index < 0) index = 0;
    node.index = index;
    return node.spec.option_labels[index];
  }

  function refresh(node) {
    if (editor && editor.node === node) return;
    node.el.textContent = displayText(node);
  }

  function text(content) {
    return document.createTextNode(content);
  }

  function makeValueSpan(name, spec) {
    const span = document.createElement("span");
    span.className = `tangle-fn__val tangle-fn__val--${spec.kind}`;
    span.dataset.name = name;
    span.tabIndex = 0;
    span.setAttribute("role", "button");
    const node = { el: span, spec, kind: spec.kind, name, index: 0 };
    nodes.set(name, node);
    refresh(node);
    span.setAttribute("aria-label", ariaLabel(node));
    return span;
  }

  function ariaLabel(node) {
    if (node.kind === "number") return `${node.name}: number, drag to change or click to type.`;
    if (node.kind === "choice") return `${node.name}: click to cycle options.`;
    return `${node.name}: click to edit text.`;
  }

  function appendArg(name, spec) {
    const key = document.createElement("span");
    key.className = "tangle-fn__key";
    key.textContent = `${name}=`;
    line.appendChild(key);
    line.appendChild(makeValueSpan(name, spec));
  }

  function layout(multiline) {
    nodes.clear();
    const order = model.get("param_order") || [];
    const parameters = model.get("parameters") || {};
    const names = order.filter((name) => parameters[name]);
    line.replaceChildren();
    if (multiline) {
      // Black-style: one argument per line, indented, with a trailing comma.
      line.appendChild(text(`${model.get("fn_name")}(\n`));
      names.forEach((name) => {
        line.appendChild(text("    "));
        appendArg(name, parameters[name]);
        line.appendChild(text(",\n"));
      });
      line.appendChild(text(")"));
    } else {
      line.appendChild(text(`${model.get("fn_name")}(`));
      names.forEach((name, i) => {
        if (i > 0) line.appendChild(text(", "));
        appendArg(name, parameters[name]);
      });
      line.appendChild(text(")"));
    }
  }

  function build() {
    closeEditor(false);
    layout(false);
    root.classList.remove("is-multiline");
    // If the single-line call overflows the configured width, wrap it.
    if (line.clientWidth > 0 && line.scrollWidth > line.clientWidth + 1) {
      layout(true);
      root.classList.add("is-multiline");
    }
  }

  // --- choice / string clicks -------------------------------------------------
  function cycleChoice(node) {
    const options = node.spec.options;
    node.index = (node.index + 1) % options.length;
    setValue(node.name, options[node.index], { flush: true });
    refresh(node);
  }

  function openEditor(node) {
    closeEditor(false);
    const values = model.get("values") || {};
    // Match the token's color exactly (measure before hiding it).
    const color = getComputedStyle(node.el).color;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "tangle-fn__editor";
    input.style.color = color;
    if (node.kind === "number") {
      input.inputMode = "decimal";
      input.value = formatNumber(values[node.name], node.spec);
    } else {
      input.value = String(values[node.name]);
    }
    const autosize = () => {
      input.style.width = "0";
      input.style.width = `${input.scrollWidth + 4}px`;
    };
    node.el.style.display = "none";
    node.el.after(input);
    editor = { node, input, autosize };
    input.addEventListener("keydown", onEditorKeydown);
    input.addEventListener("blur", onEditorBlur);
    input.addEventListener("input", autosize);
    autosize();
    input.focus();
    input.select();
  }

  function onEditorKeydown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      closeEditor(true);
    } else if (event.key === "Escape") {
      event.preventDefault();
      closeEditor(false);
    }
  }

  function onEditorBlur() {
    closeEditor(true);
  }

  function closeEditor(commit) {
    if (!editor) return;
    const { node, input, autosize } = editor;
    let committed = null;
    if (commit && node.kind === "number") {
      const parsed = Number(input.value);
      if (!Number.isFinite(parsed)) {
        input.classList.add("is-invalid");
        input.focus();
        input.select();
        return;
      }
      committed = snap(parsed, node.spec);
    } else if (commit) {
      committed = input.value;
    }
    editor = null;
    input.removeEventListener("keydown", onEditorKeydown);
    input.removeEventListener("blur", onEditorBlur);
    input.removeEventListener("input", autosize);
    input.remove();
    node.el.style.display = "";
    if (committed !== null) setValue(node.name, committed, { flush: true });
    refresh(node);
  }

  // --- number drag ------------------------------------------------------------
  function startDrag(event) {
    const target = event.target.closest(".tangle-fn__val--number");
    if (!target || (event.pointerType === "mouse" && event.button !== 0)) return;
    const node = nodes.get(target.dataset.name);
    if (!node) return;
    event.preventDefault();
    closeEditor(false);
    drag = {
      node,
      pointerId: event.pointerId,
      startX: event.clientX,
      startValue: (model.get("values") || {})[node.name],
      moved: false,
    };
    root.classList.add("is-dragging");
    node.el.classList.add("is-active");
  }

  function moveDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const deltaX = event.clientX - drag.startX;
    if (Math.abs(deltaX) >= 3) drag.moved = true;
    if (!drag.moved) return;
    event.preventDefault();
    const spec = drag.node.spec;
    const steps = Math.trunc(deltaX / spec.pixels_per_step);
    let next = clampSpec(drag.startValue + steps * spec.step, spec);
    next = spec.is_int ? Math.round(next) : roundForStep(next, spec.step);
    if ((model.get("values") || {})[drag.node.name] === next) return;
    setValue(drag.node.name, next);
    refresh(drag.node);
  }

  function endDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const finished = drag;
    drag = null;
    root.classList.remove("is-dragging");
    finished.node.el.classList.remove("is-active");
    if (finished.moved) {
      flushSave();
      return;
    }
    openEditor(finished.node);
  }

  function cancelDrag(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    drag.node.el.classList.remove("is-active");
    drag = null;
    root.classList.remove("is-dragging");
  }

  function onClick(event) {
    const target = event.target.closest(".tangle-fn__val");
    if (!target) return;
    const node = nodes.get(target.dataset.name);
    if (!node) return;
    if (node.kind === "choice") cycleChoice(node);
    else if (node.kind === "string") openEditor(node);
  }

  function onKeydown(event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    const target = event.target.closest(".tangle-fn__val");
    if (!target) return;
    const node = nodes.get(target.dataset.name);
    if (!node) return;
    event.preventDefault();
    if (node.kind === "choice") cycleChoice(node);
    else openEditor(node);
  }

  function onValuesChange() {
    if (localUpdate) {
      localUpdate = false;
      return;
    }
    nodes.forEach((node) => refresh(node));
  }

  applyTheme();
  build();
  // Re-check wrapping once the element has real width (first paint may be 0).
  requestAnimationFrame(() => {
    if (!disposed) build();
  });

  line.addEventListener("pointerdown", startDrag);
  line.addEventListener("click", onClick);
  line.addEventListener("keydown", onKeydown);
  line.addEventListener("dragstart", (event) => event.preventDefault());
  document.addEventListener("pointermove", moveDrag);
  document.addEventListener("pointerup", endDrag);
  document.addEventListener("pointercancel", cancelDrag);
  model.on("change:values", onValuesChange);
  model.on("change:parameters", build);
  model.on("change:param_order", build);
  model.on("change:fn_name", build);
  model.on("change:theme", applyTheme);
  model.on("change:width", applyTheme);

  return () => {
    disposed = true;
    clearTimeout(saveTimer);
    closeEditor(false);
    line.removeEventListener("pointerdown", startDrag);
    line.removeEventListener("click", onClick);
    line.removeEventListener("keydown", onKeydown);
    document.removeEventListener("pointermove", moveDrag);
    document.removeEventListener("pointerup", endDrag);
    document.removeEventListener("pointercancel", cancelDrag);
    model.off("change:values", onValuesChange);
    model.off("change:parameters", build);
    model.off("change:param_order", build);
    model.off("change:fn_name", build);
    model.off("change:theme", applyTheme);
    model.off("change:width", applyTheme);
  };
}

export default { render };
