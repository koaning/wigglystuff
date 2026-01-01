// js/copybutton/widget.js
const SVG_NS = "http://www.w3.org/2000/svg";
function createCopyIcon() {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 15 15");
  svg.setAttribute("class", "copy-button-icon");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute(
    "d",
    "M1 9.50006C1 10.3285 1.67157 11.0001 2.5 11.0001H4L4 10.0001H2.5C2.22386 10.0001 2 9.7762 2 9.50006L2 2.50006C2 2.22392 2.22386 2.00006 2.5 2.00006L9.5 2.00006C9.77614 2.00006 10 2.22392 10 2.50006V4.00002H5.5C4.67158 4.00002 4 4.67159 4 5.50002V12.5C4 13.3284 4.67158 14 5.5 14H12.5C13.3284 14 14 13.3284 14 12.5V5.50002C14 4.67159 13.3284 4.00002 12.5 4.00002H11V2.50006C11 1.67163 10.3284 1.00006 9.5 1.00006H2.5C1.67157 1.00006 1 1.67163 1 2.50006V9.50006ZM5 5.50002C5 5.22388 5.22386 5.00002 5.5 5.00002H12.5C12.7761 5.00002 13 5.22388 13 5.50002V12.5C13 12.7762 12.7761 13 12.5 13H5.5C5.22386 13 5 12.7762 5 12.5V5.50002Z"
  );
  path.setAttribute("fill", "currentColor");
  path.setAttribute("fill-rule", "evenodd");
  path.setAttribute("clip-rule", "evenodd");
  svg.appendChild(path);
  return svg;
}
function fallbackCopy(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "0";
  textarea.style.width = "1px";
  textarea.style.height = "1px";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);
  const ok = document.execCommand("copy");
  document.body.removeChild(textarea);
  return ok;
}
function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  return new Promise((resolve, reject) => {
    try {
      const ok = fallbackCopy(text);
      ok ? resolve() : reject(new Error("Copy command failed"));
    } catch (error) {
      reject(error);
    }
  });
}
function render({ model, el }) {
  const wrapper = document.createElement("div");
  wrapper.className = "copy-button-wrapper";
  const button = document.createElement("button");
  button.className = "copy-button";
  button.type = "button";
  button.appendChild(createCopyIcon());
  const label = document.createElement("span");
  const defaultLabel = "Copy to Clipboard";
  label.textContent = defaultLabel;
  button.appendChild(label);
  wrapper.appendChild(button);
  el.appendChild(wrapper);
  let resetTimer = null;
  const setLabel = (text) => {
    label.textContent = text;
  };
  button.addEventListener("click", () => {
    const text = model.get("text_to_copy") ?? "";
    if (resetTimer) {
      clearTimeout(resetTimer);
      resetTimer = null;
    }
    copyText(text)
      .then(() => setLabel("Copied!"))
      .catch(() => setLabel("Copy failed"))
      .finally(() => {
        resetTimer = setTimeout(() => setLabel(defaultLabel), 1200);
      });
  });
}
var widget_default = { render };
export {
  widget_default as default
};
