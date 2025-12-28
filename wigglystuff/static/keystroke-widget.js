// js/keystroke/widget.js
var containerStyles = `
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 16px;
  max-width: 360px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
`;
var canvasStyles = `
  border: 2px dashed #a7f3d0;
  border-radius: 8px;
  padding: 20px;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, SFMono, Consolas, "Liberation Mono";
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
  outline: none;
`;
function formatShortcut(keyInfo) {
  if (!keyInfo || !keyInfo.key) {
    return "Click here and press any key combination\u2026";
  }
  const modifiers = [];
  if (keyInfo.ctrlKey)
    modifiers.push("Ctrl");
  if (keyInfo.shiftKey)
    modifiers.push("Shift");
  if (keyInfo.altKey)
    modifiers.push("Alt");
  if (keyInfo.metaKey)
    modifiers.push("Meta");
  const modStr = modifiers.length ? `${modifiers.join(" + ")} + ` : "";
  return `${modStr}${keyInfo.key}`;
}
function render({ model, el }) {
  const container = document.createElement("div");
  container.style.cssText = containerStyles;
  const title = document.createElement("div");
  title.textContent = "Keyboard shortcut listener";
  title.style.fontWeight = "600";
  title.style.color = "#065f46";
  const instructions = document.createElement("div");
  instructions.style.fontSize = "14px";
  instructions.style.color = "#4b5563";
  instructions.textContent = "Click the panel below and press any shortcut.";
  const keyCanvas = document.createElement("div");
  keyCanvas.setAttribute("role", "button");
  keyCanvas.setAttribute("aria-label", "Capture keyboard shortcut");
  keyCanvas.tabIndex = 0;
  keyCanvas.style.cssText = canvasStyles;
  keyCanvas.textContent = "Click here and press any key combination\u2026";
  const metadata = document.createElement("div");
  metadata.style.fontSize = "13px";
  metadata.style.color = "#6b7280";
  metadata.style.fontFamily = '"JetBrains Mono", ui-monospace, SFMono-Regular, SFMono, Consolas, "Liberation Mono"';
  container.appendChild(title);
  container.appendChild(instructions);
  container.appendChild(keyCanvas);
  container.appendChild(metadata);
  el.appendChild(container);
  const flash = () => {
    keyCanvas.style.backgroundColor = "#ecfdf5";
    keyCanvas.style.borderColor = "#34d399";
    setTimeout(() => {
      keyCanvas.style.backgroundColor = "transparent";
      keyCanvas.style.borderColor = "#a7f3d0";
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
    keyCanvas.style.borderColor = "#34d399";
    keyCanvas.style.backgroundColor = "#f0fdf4";
  });
  keyCanvas.addEventListener("blur", () => {
    keyCanvas.style.borderColor = "#a7f3d0";
    keyCanvas.style.backgroundColor = "transparent";
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
