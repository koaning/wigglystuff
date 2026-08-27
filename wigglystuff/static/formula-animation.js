const KATEX_VERSION = "0.16.11";
const KATEX_MODULE_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.mjs`;
const KATEX_CSS_URL = `https://cdn.jsdelivr.net/npm/katex@${KATEX_VERSION}/dist/katex.min.css`;
let katexPromise = null;

function loadKatex() {
  if (!katexPromise) katexPromise = import(KATEX_MODULE_URL);
  return katexPromise;
}

function ensureKatexCss() {
  if (document.querySelector('link[data-formula-animation-katex="true"]')) return;
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = KATEX_CSS_URL;
  link.dataset.formulaAnimationKatex = "true";
  document.head.appendChild(link);
}

// Vertical gap (px) between the centered "current" line and the line above it.
const SLOT_OFFSET = 104;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
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
  root.className = `formula-animation formula-animation--theme-${model.get("theme")}`;

  const heading = document.createElement("div");
  heading.className = "formula-animation__title";

  const stage = document.createElement("div");
  stage.className = "formula-animation__stage";

  const controls = document.createElement("div");
  controls.className = "formula-animation__controls";
  controls.tabIndex = 0; // focusable: keyboard shortcuts only fire once focused.

  const prevBtn = document.createElement("button");
  prevBtn.type = "button";
  prevBtn.className = "formula-animation__btn";
  prevBtn.innerHTML = "&lsaquo;";
  prevBtn.setAttribute("aria-label", "Previous step");

  const counter = document.createElement("span");
  counter.className = "formula-animation__counter";

  const nextBtn = document.createElement("button");
  nextBtn.type = "button";
  nextBtn.className = "formula-animation__btn";
  nextBtn.innerHTML = "&rsaquo;";
  nextBtn.setAttribute("aria-label", "Next step");

  const hint = document.createElement("span");
  hint.className = "formula-animation__hint";

  controls.appendChild(prevBtn);
  controls.appendChild(counter);
  controls.appendChild(nextBtn);
  controls.appendChild(hint);

  root.appendChild(heading);
  root.appendChild(stage);
  root.appendChild(controls);
  el.replaceChildren(root);

  // Slot DOM is rebuilt whenever `steps` changes; `slots[i]` holds refs.
  let slots = [];

  function totalSteps() {
    const steps = model.get("steps") || [];
    return steps.length + (model.get("spotlight") ? 1 : 0);
  }

  function currentStep() {
    const total = totalSteps();
    return clamp(model.get("step") || 0, 0, Math.max(0, total - 1));
  }

  function buildStage() {
    const steps = model.get("steps") || [];
    stage.replaceChildren();
    slots = steps.map((line, i) => {
      const slot = document.createElement("div");
      slot.className = "formula-animation__slot";

      const formula = document.createElement("div");
      formula.className = "formula-animation__formula";
      katex.renderToString
        ? (formula.innerHTML = katex.renderToString(line.tex, {
            throwOnError: false,
            displayMode: true,
          }))
        : katex.render(line.tex, formula, { throwOnError: false, displayMode: true });

      const caption = document.createElement("p");
      caption.className = "formula-animation__caption";
      caption.textContent = line.note || "";

      slot.appendChild(formula);
      slot.appendChild(caption);
      stage.appendChild(slot);
      // The final formula is the one that gets "framed" on the spotlight step.
      return { slot, formula, caption, isFinal: i === steps.length - 1 };
    });
  }

  // Position every slot relative to the focused line, exactly like the source
  // scene: current = center, previous = up & dimmed, others parked & invisible.
  function applyLayout() {
    const steps = model.get("steps") || [];
    if (steps.length === 0) return;
    const step = currentStep();
    const spotlight = model.get("spotlight") && step >= steps.length;
    const focus = Math.min(step, steps.length - 1);

    slots.forEach(({ slot, formula, caption, isFinal }, i) => {
      const rel = i - focus;
      const current = rel === 0;
      const previous = rel === -1 && !spotlight;
      const framed = isFinal && spotlight;

      const scale = current ? (framed ? 1.15 : 1) : 0.9;
      const opacity = current ? 1 : previous ? 0.35 : 0;
      slot.style.transform = `translateY(${rel * SLOT_OFFSET}px) scale(${scale})`;
      slot.style.opacity = String(opacity);
      slot.style.pointerEvents = current || previous ? "auto" : "none";

      formula.classList.toggle("formula-animation__formula--framed", framed);
      // Caption only under the active line, and never during the spotlight.
      caption.style.opacity = current && !spotlight ? "1" : "0";
    });

    const total = totalSteps();
    counter.textContent = `${step + 1} / ${total}`;
    prevBtn.disabled = step <= 0;
    nextBtn.disabled = step >= total - 1;
  }

  function renderTitle() {
    const title = model.get("title");
    heading.textContent = title || "";
    heading.style.display = title ? "" : "none";
  }

  function applyHeight() {
    stage.style.height = `${model.get("height")}px`;
  }

  function goTo(n) {
    const total = totalSteps();
    const next = clamp(n, 0, Math.max(0, total - 1));
    if (next !== model.get("step")) {
      model.set("step", next);
      model.save_changes();
    }
  }

  function rebuild() {
    buildStage();
    applyHeight();
    applyLayout();
  }

  prevBtn.addEventListener("click", () => goTo(currentStep() - 1));
  nextBtn.addEventListener("click", () => goTo(currentStep() + 1));

  // --- Opt-in keyboard (scoped to this widget, never the whole notebook) ---
  // Arrows only work after the user clicks the controls to focus them, so we
  // never steal the notebook's arrow keys or fight other widgets for them.
  function updateHint() {
    hint.textContent =
      document.activeElement === controls
        ? "Keyboard active — ←/→ to step"
        : "Click to enable ←/→ keys";
  }
  controls.addEventListener("focus", () => {
    controls.classList.add("is-focused");
    updateHint();
  });
  controls.addEventListener("blur", () => {
    controls.classList.remove("is-focused");
    updateHint();
  });
  controls.addEventListener("keydown", (event) => {
    const total = totalSteps();
    let handled = true;
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        goTo(currentStep() + 1);
        break;
      case "ArrowLeft":
      case "ArrowUp":
        goTo(currentStep() - 1);
        break;
      case "Home":
        goTo(0);
        break;
      case "End":
        goTo(total - 1);
        break;
      default:
        handled = false;
    }
    if (handled) {
      event.preventDefault();
      event.stopPropagation();
    }
  });

  function handleThemeChange() {
    root.classList.remove(
      "formula-animation--theme-auto",
      "formula-animation--theme-light",
      "formula-animation--theme-dark",
    );
    root.classList.add(`formula-animation--theme-${model.get("theme")}`);
  }

  model.on("change:steps", rebuild);
  model.on("change:spotlight", applyLayout);
  model.on("change:step", applyLayout);
  model.on("change:height", applyHeight);
  model.on("change:title", renderTitle);
  model.on("change:theme", handleThemeChange);

  renderTitle();
  rebuild();
  updateHint();

  return () => {
    model.off("change:steps", rebuild);
    model.off("change:spotlight", applyLayout);
    model.off("change:step", applyLayout);
    model.off("change:height", applyHeight);
    model.off("change:title", renderTitle);
    model.off("change:theme", handleThemeChange);
  };
}

export default { render };
