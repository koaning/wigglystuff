// js/copybutton/widget.js
const SVG_NS = "http://www.w3.org/2000/svg";

function createCopyIcon() {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "copy-button-icon");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");

  const rectBack = document.createElementNS(SVG_NS, "rect");
  rectBack.setAttribute("x", "7");
  rectBack.setAttribute("y", "7");
  rectBack.setAttribute("width", "10");
  rectBack.setAttribute("height", "10");
  rectBack.setAttribute("rx", "2");
  rectBack.setAttribute("fill", "currentColor");
  rectBack.setAttribute("fill-opacity", "0.35");

  const rectFront = document.createElementNS(SVG_NS, "rect");
  rectFront.setAttribute("x", "4");
  rectFront.setAttribute("y", "4");
  rectFront.setAttribute("width", "10");
  rectFront.setAttribute("height", "10");
  rectFront.setAttribute("rx", "2");
  rectFront.setAttribute("fill", "currentColor");

  svg.appendChild(rectBack);
  svg.appendChild(rectFront);
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
export { widget_default as default };
