/**
 * EsmWidget – render an inline ES module in the notebook.
 *
 * The user-supplied `code` traitlet is a full ES module (standard anywidget
 * contract: `export default { render }`). We load it as a real module via a
 * Blob URL + dynamic `import()`, so top-level `import` statements work and the
 * user can pull any library from a CDN:
 *
 *     import { animate } from "https://cdn.jsdelivr.net/npm/motion@12/+esm";
 *     export default {
 *       render({ model, el }) {
 *         const box = document.createElement("div");
 *         el.appendChild(box);
 *         model.on("change:data", () => animate(box, { x: model.get("data").x }));
 *       }
 *     };
 *
 * The `data` traitlet is synced both ways. Changing it does NOT re-run the
 * module — the module observes `change:data` itself — so animation libraries can
 * tween toward the new state instead of restarting.
 */

// Turn an ES module string into a module via a Blob URL. Real `import()` means
// top-level static `import` statements inside the code resolve correctly.
async function loadModule(code) {
  const url = URL.createObjectURL(new Blob([code], { type: "text/javascript" }));
  try {
    return await import(/* webpackIgnore: true */ /* @vite-ignore */ url);
  } finally {
    URL.revokeObjectURL(url);
  }
}

function render({ model, el }) {
  el.classList.add("esm-widget-root");

  const styleEl = document.createElement("style");
  el.appendChild(styleEl);

  const container = document.createElement("div");
  container.className = "esm-widget-container";
  el.appendChild(container);

  const errorBox = document.createElement("pre");
  errorBox.className = "esm-widget-error";
  errorBox.style.display = "none";
  el.appendChild(errorBox);

  // Bumped on every (re)run so a stale async run can't clobber a newer one.
  let runToken = 0;
  // Cleanup returned by the user module's render, invoked before each re-run.
  let userCleanup = null;

  function applySize() {
    container.style.width = model.get("width") + "px";
    container.style.height = model.get("height") + "px";
  }

  function applyCss() {
    styleEl.textContent = model.get("css") || "";
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
    model.set("error", message);
    model.save_changes();
  }

  function clearError() {
    errorBox.textContent = "";
    errorBox.style.display = "none";
    if (model.get("error")) {
      model.set("error", "");
      model.save_changes();
    }
  }

  function runCleanup() {
    if (typeof userCleanup === "function") {
      try {
        userCleanup();
      } catch (err) {
        // A failing cleanup shouldn't block the next run.
      }
    }
    userCleanup = null;
  }

  async function run() {
    const token = ++runToken;
    runCleanup();
    clearError();
    container.innerHTML = "";

    const code = model.get("code");
    if (!code) return;

    let mod;
    try {
      mod = await loadModule(code);
    } catch (err) {
      if (token !== runToken) return;
      showError("Failed to load module: " + ((err && err.stack) || String(err)));
      return;
    }
    if (token !== runToken) return;

    // Accept `export default { render }`, `export default () => ({ render })`,
    // and the legacy bare `export function render`.
    let def = mod.default;
    if (typeof def === "function") {
      try {
        def = await def();
      } catch (err) {
        if (token !== runToken) return;
        showError((err && err.stack) || String(err));
        return;
      }
    }
    const renderFn = (def && def.render) || mod.render;
    if (typeof renderFn !== "function") {
      showError("Module must export a default `{ render }` (or a `render` function).");
      return;
    }

    try {
      const cleanup = await renderFn({ model, el: container });
      if (token !== runToken) {
        // A newer run started while we were rendering; discard this one.
        if (typeof cleanup === "function") cleanup();
        return;
      }
      userCleanup = cleanup;
    } catch (err) {
      if (token !== runToken) return;
      showError((err && err.stack) || String(err));
    }
  }

  applySize();
  applyCss();
  run();

  // Re-run when the module or its styling changes; resize without nuking the
  // DOM; leave `data` to the module itself (that's the whole point).
  model.on("change:code", run);
  model.on("change:css", applyCss);
  model.on("change:width", applySize);
  model.on("change:height", applySize);

  return () => {
    // Invalidate any in-flight run and tear down the user module.
    runToken++;
    runCleanup();
  };
}

export default { render };
