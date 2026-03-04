// SVG icons (14x14, stroke-based)
const ICONS = {
  previous:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
  accept:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  fail:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  defer:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>',
  save:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>',
  mic:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>',
};

// Standard gamepad face button colors (Xbox-style)
const GP_BUTTON_COLORS = { 0: "gp-green", 1: "gp-red", 2: "gp-blue", 3: "gp-yellow" };

// Inline SVG of a simple gamepad outline with labeled face buttons
function gamepadDiagram(mapping) {
  // Map button indices to positions on face button diamond (right side of pad)
  // Standard layout: 0=bottom(A), 1=right(B), 2=left(X), 3=top(Y)
  const facePositions = {
    0: { cx: 148, cy: 42 }, // A - bottom
    1: { cx: 160, cy: 30 }, // B - right
    2: { cx: 136, cy: 30 }, // X - left
    3: { cx: 148, cy: 18 }, // Y - top
  };

  let faceButtons = "";
  for (const [idx, pos] of Object.entries(facePositions)) {
    const action = mapping[idx];
    const color = GP_BUTTON_COLORS[idx] || "";
    const cls = `annotation-gamepad-legend-btn ${color}`;
    // SVG circle for each button
    const strokeColor =
      idx === "0"
        ? "#16a34a"
        : idx === "1"
          ? "#dc2626"
          : idx === "2"
            ? "#3b82f6"
            : "#d97706";
    faceButtons += `<circle cx="${pos.cx}" cy="${pos.cy}" r="5" fill="none" stroke="${strokeColor}" stroke-width="1.5"/>`;
    if (action) {
      faceButtons += `<text x="${pos.cx}" y="${pos.cy + 1}" text-anchor="middle" dominant-baseline="central" fill="${strokeColor}" font-size="5" font-weight="600">${action.charAt(0).toUpperCase()}</text>`;
    }
  }

  return `<svg class="annotation-gamepad-diagram" width="120" height="48" viewBox="60 6 130 48" xmlns="http://www.w3.org/2000/svg">
    <!-- Gamepad body -->
    <path d="M80,15 Q80,10 85,10 L155,10 Q160,10 160,15 L162,35 Q163,48 155,50 L145,50 Q138,50 135,40 L130,30 Q128,26 125,26 L115,26 Q112,26 110,30 L105,40 Q102,50 95,50 L85,50 Q77,48 78,35 Z"
      fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
    <!-- D-pad cross -->
    <rect x="87" y="25" width="4" height="14" rx="1" fill="currentColor" opacity="0.15"/>
    <rect x="82" y="30" width="14" height="4" rx="1" fill="currentColor" opacity="0.15"/>
    <!-- Face buttons -->
    ${faceButtons}
    <!-- Shoulder buttons (L/R) -->
    <rect x="82" y="8" width="18" height="4" rx="2" fill="currentColor" opacity="0.15"/>
    <rect x="140" y="8" width="18" height="4" rx="2" fill="currentColor" opacity="0.15"/>
    ${mapping["4"] ? `<text x="91" y="10" text-anchor="middle" dominant-baseline="central" font-size="4" fill="currentColor" opacity="0.5">L</text>` : ""}
    ${mapping["5"] ? `<text x="149" y="10" text-anchor="middle" dominant-baseline="central" font-size="4" fill="currentColor" opacity="0.5">R</text>` : ""}
  </svg>`;
}

function render({ model, el }) {
  el.classList.add("annotation-widget");

  // Apply width
  function applyWidth() {
    const w = model.get("width");
    el.style.width = w + "px";
    el.style.maxWidth = "100%";
  }
  applyWidth();

  // --- State ---
  let gamepadConnected = false;
  let lastGamepadState = null;
  let recognition = null;
  let animFrameId = null;

  // --- DOM ---
  const keyArea = document.createElement("div");
  keyArea.className = "annotation-key-area";
  keyArea.tabIndex = 0;
  keyArea.setAttribute("role", "button");
  keyArea.setAttribute("aria-label", "Click to enable keyboard shortcuts");
  keyArea.textContent = "Click to enable keyboard shortcuts";

  const btnRow = document.createElement("div");
  btnRow.className = "annotation-btn-row";

  const noteRow = document.createElement("div");
  noteRow.className = "annotation-note-row";

  const noteInput = document.createElement("input");
  noteInput.type = "text";
  noteInput.className = "annotation-note-input";
  noteInput.placeholder = "Add a note\u2026";
  noteInput.value = model.get("note") || "";

  const micBtn = document.createElement("button");
  micBtn.className = "annotation-mic-btn";
  micBtn.innerHTML = ICONS.mic;
  micBtn.title = "Toggle speech-to-text";

  noteRow.appendChild(noteInput);
  noteRow.appendChild(micBtn);

  // Footer: save button + status
  const footer = document.createElement("div");
  footer.className = "annotation-footer";

  const saveBtn = document.createElement("button");
  saveBtn.className = "annotation-save-btn";
  saveBtn.innerHTML = ICONS.save + " Save";
  saveBtn.addEventListener("click", () => triggerAction("save"));

  const statusArea = document.createElement("div");
  statusArea.className = "annotation-status";

  const shortcutHints = document.createElement("span");

  const gamepadStatusSpan = document.createElement("span");
  gamepadStatusSpan.style.display = "flex";
  gamepadStatusSpan.style.alignItems = "center";
  gamepadStatusSpan.style.gap = "4px";
  const gamepadDot = document.createElement("span");
  gamepadDot.className = "annotation-gamepad-dot";
  const gamepadLabel = document.createTextNode("No gamepad");
  gamepadStatusSpan.appendChild(gamepadDot);
  gamepadStatusSpan.appendChild(gamepadLabel);

  statusArea.appendChild(shortcutHints);
  statusArea.appendChild(gamepadStatusSpan);

  footer.appendChild(saveBtn);
  footer.appendChild(statusArea);

  // Gamepad mapping panel (hidden until connected)
  const gamepadMap = document.createElement("div");
  gamepadMap.className = "annotation-gamepad-map";

  el.appendChild(keyArea);
  el.appendChild(btnRow);
  el.appendChild(noteRow);
  el.appendChild(footer);
  el.appendChild(gamepadMap);

  // --- Button rendering (excludes "save" — that's in the footer) ---
  let buttonEls = {};

  function buildButtons() {
    btnRow.innerHTML = "";
    buttonEls = {};
    const actions = model.get("actions") || [];
    actions.forEach((name) => {
      if (name === "save") return; // save is in footer
      const btn = document.createElement("button");
      btn.className = "annotation-btn annotation-btn-" + name.toLowerCase();
      const icon = ICONS[name.toLowerCase()];
      btn.innerHTML = (icon || "") + " " + name;
      btn.addEventListener("click", () => triggerAction(name));
      btnRow.appendChild(btn);
      buttonEls[name] = btn;
    });
  }

  function updateShortcutHints() {
    const mapping = model.get("keyboard_mapping") || {};
    const reversed = {};
    for (const [key, action] of Object.entries(mapping)) {
      reversed[action] = key;
    }
    const actions = model.get("actions") || [];
    const hints = actions
      .filter((a) => reversed[a])
      .map((a) => reversed[a] + ":" + a)
      .join("  ");
    const micHint = reversed["mic"] ? "  " + reversed["mic"] + ":mic" : "";
    shortcutHints.textContent = hints + micHint;
  }

  function updateGamepadMap() {
    const mapping = model.get("gamepad_mapping") || {};
    if (!gamepadConnected) {
      gamepadMap.classList.remove("is-visible");
      return;
    }
    gamepadMap.classList.add("is-visible");

    // Build legend items
    const legendItems = Object.entries(mapping)
      .filter(([, action]) => action !== "mic")
      .map(([idx, action]) => {
        const colorClass = GP_BUTTON_COLORS[idx] || "";
        return `<div class="annotation-gamepad-legend-item">
          <span class="annotation-gamepad-legend-btn ${colorClass}">${idx}</span>
          <span>${action}</span>
        </div>`;
      })
      .join("");

    gamepadMap.innerHTML = `<div class="annotation-gamepad-map-inner">
      ${gamepadDiagram(mapping)}
      <div class="annotation-gamepad-legend">${legendItems}</div>
    </div>`;
  }

  buildButtons();
  updateShortcutHints();

  // --- Action trigger ---
  function triggerAction(name) {
    if (name === "mic") {
      toggleListening();
      return;
    }
    model.set("action", name);
    model.set("action_timestamp", Date.now());
    model.save_changes();

    // Flash the button
    const btn = name === "save" ? saveBtn : buttonEls[name];
    if (btn) {
      btn.classList.add("is-flash");
      setTimeout(() => btn.classList.remove("is-flash"), 200);
    }
  }

  // --- Keyboard handling (click-to-focus) ---
  keyArea.addEventListener("click", () => keyArea.focus());
  keyArea.addEventListener("focus", () => {
    keyArea.classList.add("is-focused");
    keyArea.textContent = "Keyboard shortcuts active \u2014 press a key";
  });
  keyArea.addEventListener("blur", () => {
    keyArea.classList.remove("is-focused");
    keyArea.textContent = "Click to enable keyboard shortcuts";
  });

  keyArea.addEventListener("keydown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const key = event.key.toLowerCase();
    const mapping = model.get("keyboard_mapping") || {};
    const actionName = mapping[key];
    if (actionName) {
      keyArea.textContent = key + " \u2192 " + actionName;
      triggerAction(actionName);
    } else {
      keyArea.textContent = "\u201C" + event.key + "\u201D not mapped";
    }
  });

  // --- Note sync ---
  noteInput.addEventListener("input", () => {
    model.set("note", noteInput.value);
    model.save_changes();
  });

  model.on("change:note", () => {
    const val = model.get("note") || "";
    if (noteInput.value !== val) {
      noteInput.value = val;
    }
  });

  // --- Speech-to-text ---
  try {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        model.set("listening", true);
        model.save_changes();
        micBtn.classList.add("is-listening");
      };

      recognition.onresult = (event) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          const currentNote = model.get("note") || "";
          const separator = currentNote.length > 0 ? " " : "";
          const newNote = currentNote + separator + finalTranscript;
          noteInput.value = newNote;
          model.set("note", newNote);
          model.save_changes();
        }
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        model.set("listening", false);
        model.save_changes();
        micBtn.classList.remove("is-listening");
      };

      recognition.onend = () => {
        model.set("listening", false);
        model.save_changes();
        micBtn.classList.remove("is-listening");
      };
    }
  } catch (error) {
    console.error("Speech recognition not supported", error);
    recognition = null;
  }

  function toggleListening() {
    if (!recognition) return;
    if (model.get("listening")) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }

  micBtn.addEventListener("click", toggleListening);

  model.on("change:listening", () => {
    micBtn.classList.toggle("is-listening", model.get("listening"));
  });

  // --- Gamepad polling ---
  const frames = window.requestAnimationFrame;

  function updateGamepadStatus(connected, gamepad) {
    gamepadConnected = connected;
    if (connected) {
      gamepadDot.classList.add("is-connected");
      gamepadLabel.textContent = "Gamepad connected";
    } else {
      gamepadDot.classList.remove("is-connected");
      gamepadLabel.textContent = "No gamepad";
    }
    updateGamepadMap();
  }

  function gamepadLoop() {
    const gamepads = navigator.getGamepads();
    const gamepad = gamepads[0] || gamepads[1] || gamepads[2] || gamepads[3];

    if (gamepad && gamepad.connected) {
      if (!gamepadConnected) {
        updateGamepadStatus(true, gamepad);
      }

      const currentState = gamepad.buttons.map((b) => b.pressed).join("");
      if (currentState !== lastGamepadState) {
        const mapping = model.get("gamepad_mapping") || {};
        gamepad.buttons.forEach((button, i) => {
          if (button.pressed) {
            const actionName = mapping[String(i)];
            if (actionName) {
              triggerAction(actionName);
            }
          }
        });
      }
      lastGamepadState = currentState;

      const debounce = model.get("debounce_ms") || 200;
      const hasPress = gamepad.buttons.some((b) => b.pressed);
      setTimeout(
        () => {
          animFrameId = frames(gamepadLoop);
        },
        hasPress ? debounce : 50,
      );
    } else {
      if (gamepadConnected) {
        updateGamepadStatus(false);
      }
      setTimeout(() => {
        animFrameId = frames(gamepadLoop);
      }, 100);
    }
  }

  window.addEventListener("gamepadconnected", (e) => {
    updateGamepadStatus(true, e.gamepad);
  });
  window.addEventListener("gamepaddisconnected", () => {
    updateGamepadStatus(false);
  });

  updateGamepadStatus(false);
  animFrameId = frames(gamepadLoop);

  // --- React to model changes ---
  model.on("change:actions", () => {
    buildButtons();
    updateShortcutHints();
  });

  model.on("change:keyboard_mapping", updateShortcutHints);
  model.on("change:gamepad_mapping", updateGamepadMap);
  model.on("change:width", applyWidth);

  // --- Cleanup ---
  return () => {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    if (recognition && model.get("listening")) {
      try {
        recognition.stop();
      } catch (_) {}
    }
  };
}

export default { render };
