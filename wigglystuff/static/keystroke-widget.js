// js/keystroke/widget.js
function formatShortcut(keyInfo) {
  if (!keyInfo || !keyInfo.key) {
    return "Click here and press any key combination\u2026";
  }
  const modifiers = [];
  if (keyInfo.ctrlKey) modifiers.push("Ctrl");
  if (keyInfo.shiftKey) modifiers.push("Shift");
  if (keyInfo.altKey) modifiers.push("Alt");
  if (keyInfo.metaKey) modifiers.push("Meta");
  const modStr = modifiers.length ? `${modifiers.join(" + ")} + ` : "";
  return `${modStr}${keyInfo.key}`;
}
function render({ model, el }) {
  const container = document.createElement("div");
  container.className = "keystroke-widget";
  const title = document.createElement("div");
  title.textContent = "Keyboard shortcut listener";
  title.className = "keystroke-title";
  const instructions = document.createElement("div");
  instructions.className = "keystroke-instructions";
  instructions.textContent = "Click the panel below and press any shortcut.";
  const keyCanvas = document.createElement("div");
  keyCanvas.setAttribute("role", "button");
  keyCanvas.setAttribute("aria-label", "Capture keyboard shortcut");
  keyCanvas.tabIndex = 0;
  keyCanvas.className = "keystroke-canvas";
  keyCanvas.textContent = "Click here and press any key combination\u2026";
  const metadata = document.createElement("div");
  metadata.className = "keystroke-meta";
  container.appendChild(title);
  container.appendChild(instructions);
  container.appendChild(keyCanvas);
  container.appendChild(metadata);
  el.appendChild(container);
  const flash = () => {
    keyCanvas.classList.add("is-flash");
    setTimeout(() => {
      keyCanvas.classList.remove("is-flash");
    }, 200);
  };
  const updateDisplay = (info) => {
    keyCanvas.textContent = formatShortcut(info);
    if (info && info.code) {
      metadata.innerHTML = `
        Code: ${info.code}<br>
        Timestamp: ${info.timestamp || "\u2014"}
      `;
    } else {
      metadata.textContent = "No keystrokes recorded yet.";
    }
  };
  keyCanvas.addEventListener("click", () => keyCanvas.focus());
  keyCanvas.addEventListener("focus", () => {
    keyCanvas.classList.add("is-focused");
  });
  keyCanvas.addEventListener("blur", () => {
    keyCanvas.classList.remove("is-focused");
  });
  keyCanvas.addEventListener("keydown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const keyInfo = {
      key: event.key,
      code: event.code,
      ctrlKey: event.ctrlKey,
      shiftKey: event.shiftKey,
      altKey: event.altKey,
      metaKey: event.metaKey,
      timestamp: Date.now()
    };
    model.set("last_key", keyInfo);
    model.save_changes();
    updateDisplay(keyInfo);
    flash();
  });
  model.on("change:last_key", () => updateDisplay(model.get("last_key")));
  updateDisplay(model.get("last_key"));
}
var widget_default = { render };
export {
  widget_default as default
};
