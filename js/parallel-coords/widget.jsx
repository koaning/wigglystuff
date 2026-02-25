import React from "react";
import ReactDOM from "react-dom/client";
import {
  HiPlot,
  Experiment,
  DefaultPlugins,
  createDefaultPlugins,
  PersistentStateInMemory,
} from "hiplot";

// Only show the parallel plot plugin (no XY, distribution, or table)
const plugins = (() => {
  const p = createDefaultPlugins();
  delete p[DefaultPlugins.XY];
  delete p[DefaultPlugins.DISTRIBUTION];
  delete p[DefaultPlugins.TABLE];
  return p;
})();

const CATEGORICAL_COLOR_SCHEME = [
  "rgb(31, 119, 180)",
  "rgb(255, 127, 14)",
  "rgb(214, 39, 40)",
  "rgb(148, 103, 189)",
  "rgb(140, 86, 75)",
  "rgb(227, 119, 194)",
  "rgb(127, 127, 127)",
  "rgb(188, 189, 34)",
  "rgb(23, 190, 207)",
  "rgb(31, 119, 180)",
  "rgb(174, 199, 232)",
  "rgb(255, 187, 120)",
  "rgb(255, 152, 150)",
  "rgb(197, 176, 213)",
  "rgb(196, 156, 148)",
  "rgb(247, 182, 210)",
  "rgb(199, 199, 199)",
  "rgb(219, 219, 141)",
  "rgb(158, 218, 229)",
  "rgb(44, 160, 44)",
];

function render({ model, el }) {
  const root = ReactDOM.createRoot(el);
  const persistentState = {};

  function isDark() {
    const darkEl = document.querySelector(
      ".dark, .dark-theme, [data-theme='dark'], body[data-jp-theme-light='false']"
    );
    if (darkEl) return true;

    const lightEl = document.querySelector(
      ".light, .light-theme, [data-theme='light'], body[data-jp-theme-light='true']"
    );
    if (lightEl) return false;

    // Prefer explicit notebook/page theme; avoid OS-level fallback that can mismatch.
    return false;
  }

  function buildExperiment() {
    const data = model.get("data") || [];
    const colorBy = model.get("color_by") || "";
    if (!data.length) return null;
    const withUids = data.map((row, i) => ({ uid: String(i), ...row }));
    const exp = Experiment.from_iterable(withUids);
    if (colorBy) {
      exp.colorby = colorBy;
      const values = data.map((row) => row[colorBy]).filter((v) => v !== undefined && v !== null);
      const uniqueValues = Array.from(new Set(values));
      const numericValues = values
        .map((v) => (typeof v === "number" ? v : parseFloat(v)))
        .filter((v) => Number.isFinite(v));
      const allNumeric = values.length > 0 && numericValues.length === values.length;

      if (allNumeric && uniqueValues.length > 20) {
        const minValue = Math.min(...numericValues);
        const maxValue = Math.max(...numericValues);
        exp.parameters_definition[colorBy] = {
          type: "numeric",
          colors: {},
          colormap: null,
          force_value_min: minValue,
          force_value_max: maxValue,
          label_css: null,
          label_html: null,
        };
      } else {
        const colors = {};
        uniqueValues.forEach((value, idx) => {
          colors[value] = CATEGORICAL_COLOR_SCHEME[idx % CATEGORICAL_COLOR_SCHEME.length];
        });
        exp.parameters_definition[colorBy] = {
          type: "categorical",
          colors,
          colormap: null,
          force_value_min: null,
          force_value_max: null,
          label_css: null,
          label_html: null,
        };
      }
    }
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
    persistentState[`${DefaultPlugins.PARALLEL_PLOT}.height`] = height;

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
          key: (model.get("data") || []).length + "_" + (model.get("color_by") || "") + "_" + String(height),
          experiment,
          plugins,
          dark: isDark(),
          onChange: buildOnChange(),
          persistentState: new PersistentStateInMemory("", persistentState),
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
