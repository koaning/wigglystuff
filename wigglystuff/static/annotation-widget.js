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

  const saveBtn = document.createElement("button");
  saveBtn.className = "annotation-save-btn";
  saveBtn.innerHTML = ICONS.save + " Save";
  saveBtn.addEventListener("click", () => triggerAction("save"));

  noteRow.appendChild(noteInput);
  noteRow.appendChild(micBtn);
  noteRow.appendChild(saveBtn);

  // Toggle to show/hide shortcuts
  const shortcutsToggle = document.createElement("button");
  shortcutsToggle.className = "annotation-shortcuts-toggle";
  shortcutsToggle.textContent = "Show shortcuts";
  shortcutsToggle.addEventListener("click", () => {
    const visible = shortcutsPanel.classList.toggle("is-visible");
    shortcutsToggle.textContent = visible ? "Hide shortcuts" : "Show shortcuts";
  });

  // Shortcuts panel: keyboard (left) + gamepad (right)
  const shortcutsPanel = document.createElement("div");
  shortcutsPanel.className = "annotation-shortcuts";

  // Top bar: gamepad status (right-aligned)
  const topBar = document.createElement("div");
  topBar.className = "annotation-top-bar";
  const gamepadDot = document.createElement("span");
  gamepadDot.className = "annotation-gamepad-dot";
  const gamepadLabel = document.createElement("span");
  gamepadLabel.className = "annotation-gamepad-label";
  gamepadLabel.textContent = "";
  topBar.appendChild(gamepadDot);
  topBar.appendChild(gamepadLabel);
  topBar.style.display = "none";

  el.appendChild(topBar);
  el.appendChild(keyArea);
  el.appendChild(btnRow);
  el.appendChild(noteRow);
  el.appendChild(shortcutsToggle);
  el.appendChild(shortcutsPanel);

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

  function updateShortcuts() {
    // Desired action order
    const actionOrder = ["previous", "accept", "fail", "defer", "mic", "save"];

    // Reverse keyboard mapping: action -> key
    const kbMapping = model.get("keyboard_mapping") || {};
    const kbByAction = {};
    for (const [key, action] of Object.entries(kbMapping)) {
      kbByAction[action] = key;
    }
    const kbItems = actionOrder
      .filter((a) => kbByAction[a])
      .map((action) => `<div class="annotation-sc-row sc-${action}"><kbd>${kbByAction[action]}</kbd><span>${action}</span></div>`)
      .join("");

    // Gamepad: reverse mapping, same action order
    let gpSection = "";
    if (gamepadConnected) {
      const gpMapping = model.get("gamepad_mapping") || {};
      const gpByAction = {};
      for (const [idx, action] of Object.entries(gpMapping)) {
        gpByAction[action] = idx;
      }
      const gpItems = actionOrder
        .filter((a) => gpByAction[a])
        .map((action) => `<div class="annotation-sc-row sc-${action}" data-btn="${gpByAction[action]}"><kbd>${gpByAction[action]}</kbd><span>${action}</span></div>`)
        .join("");
      gpSection = `<div class="annotation-sc-header">Gamepad</div>
        <div class="annotation-sc-grid">${gpItems}</div>`;
    }

    shortcutsPanel.innerHTML = `<div class="annotation-sc-header">Keyboard</div>
      <div class="annotation-sc-grid">${kbItems}</div>
      ${gpSection}`;
  }

  buildButtons();
  updateShortcuts();

  // --- Disabled state ---
  function applyDisabled() {
    el.classList.toggle("is-disabled", !!model.get("disabled"));
  }
  applyDisabled();
  model.on("change:disabled", applyDisabled);

  // --- Action trigger ---
  function triggerAction(name) {
    if (model.get("disabled") && name !== "previous" && name !== "save") return;
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

  let keyFadeTimer = null;
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
    // Reset text after a moment
    clearTimeout(keyFadeTimer);
    keyFadeTimer = setTimeout(() => {
      keyArea.textContent = "Keyboard shortcuts active \u2014 press a key";
    }, 350);
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
    // Keep speech base text in sync so mic appends to the correct value
    noteBeforeSpeech = val;
  });

  // --- Speech-to-text ---
  let noteBeforeSpeech = "";
  try {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        noteBeforeSpeech = model.get("note") || "";
        model.set("listening", true);
        model.save_changes();
        micBtn.classList.add("is-listening");
      };

      recognition.onresult = (event) => {
        let finalTranscript = "";
        let interimTranscript = "";
        for (let i = 0; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        // Build the full note: base + final + interim preview
        const base = noteBeforeSpeech;
        const separator = base.length > 0 ? " " : "";
        const confirmed = finalTranscript ? separator + finalTranscript : "";
        const preview = interimTranscript
          ? (base.length > 0 || finalTranscript ? " " : "") + interimTranscript
          : "";
        const newNote = base + confirmed + preview;
        noteInput.value = newNote;
        // Only sync finalized text to the model
        if (finalTranscript) {
          const finalNote = base + confirmed;
          noteBeforeSpeech = finalNote;
          model.set("note", finalNote);
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
    if (!recognition) {
      micBtn.classList.add("is-unavailable");
      micBtn.title = "Speech recognition not supported in this browser";
      return;
    }
    if (model.get("listening")) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }

  if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
    micBtn.classList.add("is-unavailable");
    micBtn.title = "Speech recognition not supported in this browser";
  }

  micBtn.addEventListener("click", toggleListening);

  model.on("change:listening", () => {
    micBtn.classList.toggle("is-listening", model.get("listening"));
  });

  // --- Gamepad polling ---
  const frames = window.requestAnimationFrame;

  function updateGamepadStatus(connected) {
    gamepadConnected = connected;
    if (connected) {
      gamepadDot.classList.add("is-connected");
      gamepadLabel.textContent = "Gamepad connected";
      topBar.style.display = "";
    } else {
      gamepadDot.classList.remove("is-connected");
      gamepadLabel.textContent = "";
      topBar.style.display = "none";
    }
    updateShortcuts();
  }

  function gamepadLoop() {
    const gamepads = navigator.getGamepads();
    const gamepad = gamepads[0] || gamepads[1] || gamepads[2] || gamepads[3];

    if (gamepad && gamepad.connected) {
      if (!gamepadConnected) {
        updateGamepadStatus(true, gamepad);
      }

      const currentState = gamepad.buttons.map((b) => b.pressed).join("");

      // Live press highlighting on the shortcuts panel
      gamepad.buttons.forEach((button, i) => {
        const el = shortcutsPanel.querySelector(`[data-btn="${i}"]`);
        if (el) el.classList.toggle("is-active", button.pressed);
      });

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
    updateShortcuts();
  });

  model.on("change:keyboard_mapping", updateShortcuts);
  model.on("change:gamepad_mapping", updateShortcuts);
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
