// node_modules/@anywidget/react/index.js
import * as React from "react";
import * as ReactDOM from "react-dom/client";
var RenderContext = React.createContext(
  /** @type {any} */
  null
);
function useRenderContext() {
  let ctx = React.useContext(RenderContext);
  if (!ctx) throw new Error("RenderContext not found");
  return ctx;
}
function useModel() {
  let ctx = useRenderContext();
  return ctx.model;
}
function useModelState(key) {
  let model = useModel();
  let [value, setValue] = React.useState(model.get(key));
  React.useEffect(() => {
    let callback = () => setValue(model.get(key));
    model.on(`change:${key}`, callback);
    return () => model.off(`change:${key}`, callback);
  }, [model, key]);
  return [
    value,
    (value2) => {
      model.set(key, value2);
      model.save_changes();
    }
  ];
}
function createRender(Widget) {
  return ({ el, model, experimental }) => {
    let root = ReactDOM.createRoot(el);
    root.render(
      React.createElement(
        React.StrictMode,
        null,
        React.createElement(
          RenderContext.Provider,
          { value: { model, experimental } },
          React.createElement(Widget)
        )
      )
    );
    return () => root.unmount();
  };
}

// node_modules/@radix-ui/react-icons/dist/react-icons.esm.js
import { forwardRef, createElement as createElement2 } from "react";
function _objectWithoutPropertiesLoose(source, excluded) {
  if (source == null) return {};
  var target = {};
  var sourceKeys = Object.keys(source);
  var key, i;
  for (i = 0; i < sourceKeys.length; i++) {
    key = sourceKeys[i];
    if (excluded.indexOf(key) >= 0) continue;
    target[key] = source[key];
  }
  return target;
}
var _excluded$1h = ["color"];
var CopyIcon = /* @__PURE__ */ forwardRef(function(_ref, forwardedRef) {
  var _ref$color = _ref.color, color = _ref$color === void 0 ? "currentColor" : _ref$color, props = _objectWithoutPropertiesLoose(_ref, _excluded$1h);
  return createElement2("svg", Object.assign({
    width: "15",
    height: "15",
    viewBox: "0 0 15 15",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg"
  }, props, {
    ref: forwardedRef
  }), createElement2("path", {
    d: "M1 9.50006C1 10.3285 1.67157 11.0001 2.5 11.0001H4L4 10.0001H2.5C2.22386 10.0001 2 9.7762 2 9.50006L2 2.50006C2 2.22392 2.22386 2.00006 2.5 2.00006L9.5 2.00006C9.77614 2.00006 10 2.22392 10 2.50006V4.00002H5.5C4.67158 4.00002 4 4.67159 4 5.50002V12.5C4 13.3284 4.67158 14 5.5 14H12.5C13.3284 14 14 13.3284 14 12.5V5.50002C14 4.67159 13.3284 4.00002 12.5 4.00002H11V2.50006C11 1.67163 10.3284 1.00006 9.5 1.00006H2.5C1.67157 1.00006 1 1.67163 1 2.50006V9.50006ZM5 5.50002C5 5.22388 5.22386 5.00002 5.5 5.00002H12.5C12.7761 5.00002 13 5.22388 13 5.50002V12.5C13 12.7762 12.7761 13 12.5 13H5.5C5.22386 13 5 12.7762 5 12.5V5.50002Z",
    fill: color,
    fillRule: "evenodd",
    clipRule: "evenodd"
  }));
});

// js/copybutton/widget.tsx
import { jsx, jsxs } from "react/jsx-runtime";
function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
}
function CopyToClipboardButton() {
  let [text_to_copy, setTextToCopy] = useModelState("text_to_copy");
  return /* @__PURE__ */ jsx("div", { className: "copy-button-wrapper", children: /* @__PURE__ */ jsxs(
    "button",
    {
      className: "copy-button",
      onClick: () => copyToClipboard(text_to_copy),
      type: "button",
      children: [
        /* @__PURE__ */ jsx(CopyIcon, { className: "copy-button-icon" }),
        "Copy to Clipboard"
      ]
    }
  ) });
}
var render = createRender(CopyToClipboardButton);
var widget_default = { render };
export {
  widget_default as default
};
