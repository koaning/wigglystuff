import React from "react";
import ReactDOM from "react-dom/client";
import {
  HiPlot,
  Experiment,
  DefaultPlugins,
  ParallelPlot,
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

/** Convert any CSS color string to "rgb(r, g, b)" format. */
function toRgbString(cssColor) {
  if (cssColor.startsWith("rgb(")) return cssColor;
  const ctx = document.createElement("canvas").getContext("2d");
  ctx.fillStyle = cssColor;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
  return `rgb(${r}, ${g}, ${b})`;
}

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
  const hiplotRef = React.createRef();
  const persistentState = {};
  let domObserver = null;
  let themeObserver = null;
  let labelDragGuardInstalled = false;
  let lastRenderedDark = null;

  function applyHeaderLayout() {
    const headerRow = el.querySelector(".pc-wrapper .container-fluid .d-flex.flex-wrap");
    if (!headerRow) return;

    headerRow.style.display = "flex";
    headerRow.style.flexWrap = "nowrap";
    headerRow.style.alignItems = "center";
    headerRow.style.columnGap = "0.35rem";

    const groups = Array.from(headerRow.children).filter(
      (node) => node instanceof HTMLElement && node.tagName === "DIV"
    );
    const buttonGroup = groups.find((node) => node.querySelector("button"));
    const selectedGroup = groups.find((node) => (node.textContent || "").includes("Selected:"));

    if (buttonGroup) {
      buttonGroup.style.display = "flex";
      buttonGroup.style.alignItems = "center";
      buttonGroup.style.gap = "0.5rem";
      const buttons = buttonGroup.querySelectorAll("button.btn.btn-sm");
      buttons.forEach((btn, idx) => {
        btn.style.marginRight = idx === buttons.length - 1 ? "0" : "6px";
      });
    }

    if (selectedGroup) {
      selectedGroup.style.display = "flex";
      selectedGroup.style.alignItems = "center";
      selectedGroup.style.marginLeft = "8px";
      const stat = selectedGroup.querySelector("div");
      if (stat) {
        stat.style.margin = "0";
        stat.style.whiteSpace = "nowrap";
        stat.style.fontSize = "12px";
      }
    }
  }

  function ensureDomObserver() {
    if (domObserver) return;
    domObserver = new MutationObserver(() => {
      applyHeaderLayout();
    });
    domObserver.observe(el, { childList: true, subtree: true });
  }

  function ensureThemeObserver() {
    if (themeObserver) return;
    themeObserver = new MutationObserver(() => {
      const darkNow = isDark();
      if (darkNow !== lastRenderedDark) {
        doRender();
      }
    });
    const observerOpts = {
      attributes: true,
      attributeFilter: ["class", "data-theme", "data-jp-theme-light"],
    };
    if (document.documentElement) {
      themeObserver.observe(document.documentElement, observerOpts);
    }
    if (document.body) {
      themeObserver.observe(document.body, observerOpts);
    }
    let node = el.parentElement;
    while (node) {
      themeObserver.observe(node, observerOpts);
      node = node.parentElement;
    }
  }

  function getParallelPlotPlugin() {
    try {
      if (!hiplotRef.current || typeof hiplotRef.current.getPlugin !== "function") {
        return null;
      }
      return hiplotRef.current.getPlugin(ParallelPlot);
    } catch (_error) {
      return null;
    }
  }

  function ensureLabelDragGuard() {
    if (labelDragGuardInstalled) return;

    const onPointerDown = (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      const label = target.closest(".label-name");
      if (!label || !el.contains(label)) return;

      const plugin = getParallelPlotPlugin();
      if (!plugin || typeof plugin.xscale !== "function") return;

      const dimensionEl = label.closest(".dimension");
      const dimension = dimensionEl?.__data__;
      if (!dimension) return;

      const origin = Number(plugin.xscale(dimension));
      if (!Number.isFinite(origin)) return;

      // HiPlot's drag handlers assume dragging is always non-null.
      plugin.state = {
        ...plugin.state,
        dragging: {
          col: dimension,
          pos: origin,
          origin,
          dragging: false,
        },
      };
    };

    el.addEventListener("pointerdown", onPointerDown, true);
    labelDragGuardInstalled = true;

    // Stash cleanup handles on the element so we can remove listeners in widget dispose.
    el.__pcCleanupLabelDragGuard = () => {
      el.removeEventListener("pointerdown", onPointerDown, true);
      labelDragGuardInstalled = false;
    };
  }

  function isDark() {
    const darkMatcher =
      ".dark, .dark-theme, [data-theme='dark'], [data-jp-theme-light='false']";
    const lightMatcher =
      ".light, .light-theme, [data-theme='light'], [data-jp-theme-light='true']";

    // Prefer nearest explicit theme marker around this widget container.
    let node = el;
    while (node) {
      if (node.matches?.(darkMatcher)) return true;
      if (node.matches?.(lightMatcher)) return false;
      node = node.parentElement;
    }

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
      const uniqueValues = Array.from(new Set(values)).sort();
      const colorMap = model.get("color_map") || {};
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
          if (colorMap[value]) {
            colors[value] = toRgbString(colorMap[value]);
          } else {
            colors[value] = CATEGORICAL_COLOR_SCHEME[idx % CATEGORICAL_COLOR_SCHEME.length];
          }
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
      brush_extents: (_type, extents) => {
        model.set("brush_extents", extents);
        model.save_changes();
      },
      filtered_uids: (_type, uids) => {
        model.set("filtered_uids", uids);
        model.save_changes();
      },
      selected_uids: (_type, uids) => {
        model.set("selected_uids", uids);
        model.save_changes();
      },
    };
  }

  function doRender() {
    const experiment = buildExperiment();
    const height = model.get("height") || 600;
    const width = model.get("width") || 0;
    const dark = isDark();
    persistentState[`${DefaultPlugins.PARALLEL_PLOT}.height`] = height;
    lastRenderedDark = dark;

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
        style: { width: width > 0 ? `${width}px` : "100%" },
      },
        React.createElement(HiPlot, {
          ref: hiplotRef,
          key:
            (model.get("data") || []).length +
            "_" +
            (model.get("color_by") || "") +
            "_" +
            JSON.stringify(model.get("color_map") || {}) +
            "_" +
            String(height) +
            "_" +
            (dark ? "dark" : "light"),
          experiment,
          plugins,
          dark,
          onChange: buildOnChange(),
          persistentState: new PersistentStateInMemory("", persistentState),
          asserts: false,
        })
      )
    );

    requestAnimationFrame(() => {
      applyHeaderLayout();
      ensureDomObserver();
      ensureThemeObserver();
      ensureLabelDragGuard();
    });
  }

  doRender();
  model.on("change:data", doRender);
  model.on("change:color_by", doRender);
  model.on("change:color_map", doRender);
  model.on("change:height", doRender);
  model.on("change:width", doRender);

  return () => {
    model.off("change:data", doRender);
    model.off("change:color_by", doRender);
    model.off("change:color_map", doRender);
    model.off("change:height", doRender);
    model.off("change:width", doRender);
    if (domObserver) {
      domObserver.disconnect();
      domObserver = null;
    }
    if (themeObserver) {
      themeObserver.disconnect();
      themeObserver = null;
    }
    if (typeof el.__pcCleanupLabelDragGuard === "function") {
      el.__pcCleanupLabelDragGuard();
      delete el.__pcCleanupLabelDragGuard;
    }
    root.unmount();
  };
}

export default { render };
