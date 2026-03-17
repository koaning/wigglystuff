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
 * Separate an Altair spec into a data-free spec and a map of named datasets.
 *
 * Altair specs carry data in one of two shapes:
 *   a) spec.datasets = {"data-<hash>": [...], ...}  with data.name refs in
 *      the top level or inside layer/hconcat/vconcat sub-specs
 *   b) spec.data.values = [...]
 *
 * For (a) we extract every dataset into dataMap keyed by its original name,
 * replace each dataset's array with [] in the clean spec (so Vega-Lite still
 * compiles the named sources), and leave all data.name references untouched.
 *
 * For (b) we extract the values into dataMap[DATA_NAME] and set
 * clean.data = {name: DATA_NAME}.
 *
 * Returns {cleanSpec, dataMap} where dataMap is {name: rows[]}.
 */
function prepareSpec(spec) {
  const clean = JSON.parse(JSON.stringify(spec));
  const dataMap = {};

  if (clean.datasets) {
    for (const [name, rows] of Object.entries(clean.datasets)) {
      dataMap[name] = rows;
      clean.datasets[name] = [];
    }
  } else if (clean.data && clean.data.values) {
    dataMap[DATA_NAME] = clean.data.values;
    clean.data = { name: DATA_NAME };
  }

  return { cleanSpec: clean, dataMap };
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

  async function fullEmbed(rawSpec, cleanSpec) {
    if (currentView) {
      currentView.finalize();
      currentView = null;
    }
    container.innerHTML = "";
    currentCleanSpec = null;

    const { vegaEmbed } = await loadVega();

    try {
      // Embed the full spec (with data) so the initial render is always
      // correct.  We store the data-free cleanSpec for future comparisons
      // so that subsequent data-only changes can be patched in-place.
      const result = await vegaEmbed(container, rawSpec, {
        actions: false,
        renderer: "svg",
      });
      currentView = result.view;
      currentCleanSpec = cleanSpec;
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

    const { cleanSpec, dataMap } = prepareSpec(rawSpec);

    // First render — or structural change: embed the full spec with data
    if (!currentView || !currentCleanSpec || !specStructureEqual(currentCleanSpec, cleanSpec)) {
      await fullEmbed(rawSpec, cleanSpec);
      return;
    }

    // Data-only change — patch in-place, never re-parse
    const { vega } = await loadVega();
    for (const [name, rows] of Object.entries(dataMap)) {
      currentView.change(
        name,
        vega.changeset().remove(() => true).insert(rows)
      );
    }
    currentView.run();
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
