/**
 * AltairWidget – flicker-free Altair/Vega-Lite rendering.
 *
 * Loads vega-embed from CDN on first use.  Data is stripped from the
 * Vega-Lite spec before embedding and pushed separately via the Vega View
 * changeset API.  On subsequent updates only the data is swapped —
 * vegaEmbed / vega.parse are never called again, so interactive state
 * (zoom, pan, selections) is fully preserved.
 *
 * See: https://vega.github.io/vega-lite/tutorials/streaming.html
 */

const DATA_NAME = "source";

let _vegaEmbed = null;
let _vega = null;

async function loadVega() {
  if (!_vegaEmbed) {
    // Import vega-embed and use its own re-exported vega reference.
    // Using a separately-loaded vega would create a second instance whose
    // changesets the view does not recognise.
    const embedMod = await import("https://cdn.jsdelivr.net/npm/vega-embed@6/+esm");
    _vegaEmbed = embedMod.default;
    _vega = embedMod.vega;
  }
  return { vegaEmbed: _vegaEmbed, vega: _vega };
}

/**
 * Separate an Altair spec into a data-free spec and a data array.
 *
 * Altair specs carry data in one of two shapes:
 *   a) spec.datasets = {"data-<hash>": [...]}  +  spec.data.name = "data-<hash>"
 *   b) spec.data.values = [...]
 *
 * We replace the data reference with {name: DATA_NAME} so that the
 * compiled Vega view exposes a predictable dataset we can target with
 * view.change().
 */
function prepareSpec(spec) {
  const clean = JSON.parse(JSON.stringify(spec));
  let data = null;

  if (clean.datasets) {
    const keys = Object.keys(clean.datasets);
    if (keys.length > 0) {
      data = clean.datasets[keys[0]];
    }
    delete clean.datasets;
  }

  if (clean.data && clean.data.values) {
    data = data || clean.data.values;
  }

  clean.data = { name: DATA_NAME };
  return { cleanSpec: clean, data: data || [] };
}

/**
 * Compare two *clean* (data-free) specs.  Returns true when the chart
 * structure (marks, encodings, scales, …) has not changed.
 */
function specStructureEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

function render({ model, el }) {
  el.classList.add("altair-widget-root");
  const container = document.createElement("div");
  container.className = "altair-widget-container";
  el.appendChild(container);

  let currentView = null;
  let currentCleanSpec = null;

  function applySize() {
    container.style.width = model.get("width") + "px";
    container.style.minHeight = model.get("height") + "px";
  }

  async function fullEmbed(cleanSpec, data) {
    if (currentView) {
      currentView.finalize();
      currentView = null;
    }
    container.innerHTML = "";
    currentCleanSpec = null;

    const { vegaEmbed, vega } = await loadVega();

    try {
      const result = await vegaEmbed(container, cleanSpec, {
        actions: false,
        renderer: "svg",
      });
      currentView = result.view;
      currentCleanSpec = cleanSpec;

      // Push data into the named source
      const cs = vega.changeset().insert(data);
      currentView.change(DATA_NAME, cs).run();
    } catch (err) {
      container.textContent = "Vega-Lite render error: " + err.message;
    }
  }

  async function handleSpecChange() {
    const rawSpec = model.get("spec");
    if (!rawSpec || Object.keys(rawSpec).length === 0) {
      if (currentView) {
        currentView.finalize();
        currentView = null;
      }
      container.innerHTML = "";
      currentCleanSpec = null;
      return;
    }

    const { cleanSpec, data } = prepareSpec(rawSpec);

    // First render — or structural change
    if (!currentView || !currentCleanSpec || !specStructureEqual(currentCleanSpec, cleanSpec)) {
      await fullEmbed(cleanSpec, data);
      return;
    }

    // Data-only change — patch in-place, never re-parse
    const { vega } = await loadVega();
    const cs = vega
      .changeset()
      .remove(() => true)
      .insert(data);
    currentView.change(DATA_NAME, cs).run();
  }

  applySize();
  handleSpecChange();

  model.on("change:spec", handleSpecChange);
  model.on("change:width", applySize);
  model.on("change:height", applySize);

  return () => {
    if (currentView) {
      currentView.finalize();
      currentView = null;
    }
  };
}

export default { render };
