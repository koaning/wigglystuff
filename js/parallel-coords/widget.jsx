import React from "react";
import ReactDOM from "react-dom/client";
import { HiPlot, Experiment, DefaultPlugins, createDefaultPlugins } from "hiplot";

// Only show the parallel plot plugin (no XY, distribution, or table)
const plugins = (() => {
  const p = createDefaultPlugins();
  delete p[DefaultPlugins.XY];
  delete p[DefaultPlugins.DISTRIBUTION];
  delete p[DefaultPlugins.TABLE];
  return p;
})();

function render({ model, el }) {
  const root = ReactDOM.createRoot(el);

  function isDark() {
    const darkEl = document.querySelector(".dark, .dark-theme, [data-theme='dark']");
    if (darkEl) return true;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function buildExperiment() {
    const data = model.get("data") || [];
    const colorBy = model.get("color_by") || "";
    if (!data.length) return null;
    const withUids = data.map((row, i) => ({ uid: String(i), ...row }));
    const exp = Experiment.from_iterable(withUids);
    if (colorBy) exp.colorby = colorBy;
    return exp;
  }

  function buildOnChange() {
    return {
      filtered_uids: (_type, uids) => {
        if (Array.isArray(uids)) {
          const indices = uids.map((u) => parseInt(u, 10)).filter((n) => !isNaN(n));
          model.set("filtered_indices", indices);
          model.save_changes();
        }
      },
      selected_uids: (_type, uids) => {
        if (Array.isArray(uids)) {
          const indices = uids.map((u) => parseInt(u, 10)).filter((n) => !isNaN(n));
          model.set("selected_indices", indices);
          model.save_changes();
        }
      },
    };
  }

  function doRender() {
    const experiment = buildExperiment();
    const height = model.get("height") || 600;

    if (!experiment) {
      root.render(
        React.createElement("div", {
          style: { padding: "1rem", color: "#888", fontFamily: "sans-serif" },
        }, "No data provided")
      );
      return;
    }

    // Render HiPlot WITHOUT StrictMode — HiPlot's class components
    // do heavy D3/jQuery DOM manipulation in componentDidMount that
    // breaks under StrictMode's double-mount behavior.
    root.render(
      React.createElement("div", {
        className: "pc-wrapper",
        style: { width: "100%" },
      },
        React.createElement(HiPlot, {
          key: (model.get("data") || []).length + "_" + (model.get("color_by") || ""),
          experiment,
          plugins,
          dark: isDark(),
          onChange: buildOnChange(),
          asserts: false,
        })
      )
    );
  }

  doRender();
  model.on("change:data", doRender);
  model.on("change:color_by", doRender);
  model.on("change:height", doRender);

  return () => {
    model.off("change:data", doRender);
    model.off("change:color_by", doRender);
    model.off("change:height", doRender);
    root.unmount();
  };
}

export default { render };
