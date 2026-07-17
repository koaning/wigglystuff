const KATEX_VERSION = "0.17.0";
const KATEX_MODULE_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.mjs`;
const KATEX_CSS_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css`;
let katexPromise = null;

function loadKatex() {
  if (!katexPromise) katexPromise = import(KATEX_MODULE_URL);
  return katexPromise;
}

function ensureKatexCss() {
  if (document.querySelector('link[data-latex-tangle-katex="true"]')) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = KATEX_CSS_URL;
  link.dataset.latexTangleKatex = "true";
  document.head.appendChild(link);
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
  const footer = document.createElement("div");
  footer.className = "latex-tangle__footer";
  const reset = document.createElement("button");
  reset.className = "latex-tangle__reset";
  reset.type = "button";
  reset.textContent = "Reset";
  const errorBox = document.createElement("div");
  errorBox.className = "latex-tangle__error";
  errorBox.hidden = true;

  stage.appendChild(formulaHost);
  footer.appendChild(reset);
  root.appendChild(stage);
  root.appendChild(footer);
  root.appendChild(errorBox);
  el.replaceChildren(root);

  let drag = null;
  let activeEditor = null;
  let editingName = null;
  let disposed = false;
  let localValuesUpdate = false;
  let saveTimer = null;
  let initialValues = getInitialValues();

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
        trust: (context) => context.command === "\\htmlData",
        strict: (errorCode) => (errorCode === "htmlExtension" ? "ignore" : "warn"),
      });
      setError("");
    } catch (error) {
      formulaHost.replaceChildren();
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

  stage.addEventListener("pointerdown", startDrag);
  stage.addEventListener("keydown", handleFormulaKeydown);
  stage.addEventListener("dragstart", (event) => event.preventDefault());
  reset.addEventListener("click", handleReset);
  document.addEventListener("pointermove", moveDrag);
  document.addEventListener("pointerup", endDrag);
  document.addEventListener("pointercancel", cancelDrag);
  model.on("change:values", handleValuesChange);
  model.on("change:parameters", handleParametersChange);
  model.on("change:latex", handleConfigChange);
  model.on("change:display_mode", handleConfigChange);
  model.on("change:editor", handleConfigChange);
  model.on("change:reveal_all_on_drag", handleConfigChange);
  model.on("change:theme", handleThemeChange);

  renderFormula();

  return () => {
    disposed = true;
    clearTimeout(saveTimer);
    closeEditor(false);
    stage.removeEventListener("pointerdown", startDrag);
    stage.removeEventListener("keydown", handleFormulaKeydown);
    reset.removeEventListener("click", handleReset);
    document.removeEventListener("pointermove", moveDrag);
    document.removeEventListener("pointerup", endDrag);
    document.removeEventListener("pointercancel", cancelDrag);
    model.off("change:values", handleValuesChange);
    model.off("change:parameters", handleParametersChange);
    model.off("change:latex", handleConfigChange);
    model.off("change:display_mode", handleConfigChange);
    model.off("change:editor", handleConfigChange);
    model.off("change:reveal_all_on_drag", handleConfigChange);
    model.off("change:theme", handleThemeChange);
  };
}

export default { render };
