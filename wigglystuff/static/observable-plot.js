/**
 * ObservablePlot – run Observable Plot code in the notebook.
 *
 * Loads Observable Plot (and d3) from a CDN on first use, then evaluates the
 * user-supplied JS (the `code` traitlet) the way an Observable cell would: as
 * an expression that returns a DOM node (e.g. `Plot.plot({...})`). The returned
 * node is mounted into the container.
 *
 * `Plot`, `d3`, `container`, `width`, `height`, and `model` are always in
 * scope. Each key of the `variables` traitlet is injected as an additional
 * in-scope variable, so Python-supplied data can be referenced by name:
 *
 *     Plot.plot({
 *       marks: [ Plot.barY(vacancies, { x: "month", y: "vacancies" }) ],
 *     })
 *
 * See: https://observablehq.com/plot/
 */

// Cache the CDN import promise per Plot version so the library is fetched once.
// d3 is pinned to a single major line and shared across versions.
const _plotCache = {};
let _d3 = null;

function loadPlot(version) {
  if (!_plotCache[version]) {
    _plotCache[version] = import(
      "https://cdn.jsdelivr.net/npm/@observablehq/plot@" + version + "/+esm"
    );
  }
  return _plotCache[version];
}

function loadD3() {
  if (!_d3) {
    _d3 = import("https://cdn.jsdelivr.net/npm/d3@7/+esm");
  }
  return _d3;
}

// Build the runnable function for `code`. We first try the expression form
// (Observable cell semantics: the code IS the value to render). If that is a
// syntax error — e.g. the user wrote setup statements — we fall back to a block
// form where the user is expected to `return` the node themselves.
function compile(code, names) {
  const args = ["Plot", "d3", "container", "width", "height", "model", ...names];
  try {
    return new Function(...args, "return (async () => (\n" + code + "\n))();");
  } catch (err) {
    if (err instanceof SyntaxError) {
      return new Function(...args, "return (async () => {\n" + code + "\n})();");
    }
    throw err;
  }
}

function render({ model, el }) {
  el.classList.add("observable-plot-root");

  const container = document.createElement("div");
  container.className = "observable-plot-container";
  el.appendChild(container);

  const errorBox = document.createElement("pre");
  errorBox.className = "observable-plot-error";
  errorBox.style.display = "none";
  el.appendChild(errorBox);

  // Bumped on every (re)run so a stale async run can't clobber a newer one.
  let runToken = 0;

  function applySize() {
    container.style.width = model.get("width") + "px";
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

  async function run() {
    const token = ++runToken;
    clearError();

    // `code` is already plain JavaScript — Python resolved any file/URL source.
    const code = model.get("code");
    if (!code) {
      container.replaceChildren();
      return;
    }

    let Plot, d3;
    try {
      [Plot, d3] = await Promise.all([loadPlot(model.get("version")), loadD3()]);
    } catch (err) {
      if (token !== runToken) return;
      container.replaceChildren();
      showError("Failed to load Observable Plot: " + (err && err.message ? err.message : err));
      return;
    }
    if (token !== runToken) return;

    const variables = model.get("variables") || {};
    const names = Object.keys(variables);

    // Observable Plot has no partial/incremental redraw — every run rebuilds the
    // whole SVG. To keep re-renders (e.g. a slider driving `variables`) from
    // flashing a blank frame, build into a detached `stage` and swap it into the
    // live container in a single atomic operation once the new node is ready.
    // The old chart stays visible until then.
    const stage = document.createElement("div");
    try {
      const fn = compile(code, names);
      const node = await fn(
        Plot,
        d3,
        stage,
        model.get("width"),
        model.get("height"),
        model,
        ...names.map((n) => variables[n])
      );
      if (token !== runToken) return;
      // Expression form returns the node; block form appends to `container`
      // (the stage) itself, in which case we mount the stage's contents.
      container.replaceChildren(node instanceof Node ? node : stage);
    } catch (err) {
      if (token !== runToken) return;
      container.replaceChildren();
      showError((err && err.stack) || String(err));
    }
  }

  applySize();
  run();

  model.on("change:code", run);
  model.on("change:variables", run);
  model.on("change:version", run);
  model.on("change:width", () => {
    applySize();
    run();
  });
  model.on("change:height", () => {
    applySize();
    run();
  });

  return () => {
    // Invalidate any in-flight run so it stops touching the removed DOM.
    runToken++;
  };
}

export default { render };
