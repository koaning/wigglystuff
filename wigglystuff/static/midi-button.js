// Lucide-style inline icons (24x24), matching the set in annotation-widget.js.
// Filled glyphs read better at pad size; strokes inherit currentColor.
const ICONS = {
  play: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>',
  pause:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>',
  stop: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="1.5"/></svg>',
  record:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="6"/></svg>',
  "skip-back":
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M19 5v14l-9-7zM7 5h2v14H7z"/></svg>',
  "skip-forward":
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M5 5v14l9-7zM15 5h2v14h-2z"/></svg>',
  circle:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="7"/></svg>',
  square:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>',
  triangle:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4l8 15H4z"/></svg>',
  heart:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7-4.35-9.5-8.5C.5 9 2 5.5 5.5 5.5c2 0 3.5 1.5 4.5 3 1-1.5 2.5-3 4.5-3C18 5.5 19.5 9 17.5 12.5 15 16.65 12 21 12 21z"/></svg>',
  star: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 18.8 6.2 21l1.1-6.5L2.6 9.8l6.5-.9z"/></svg>',
  bell: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
  zap: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L4 14h6l-1 8 9-12h-6z"/></svg>',
  check:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  x: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  plus: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  minus:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  power:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>',
  mic: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>',
  music:
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
};

// Shared across all buttons on the page so we only request access once.
let _midiAccessPromise = null;
function getMidiAccess() {
  if (!navigator.requestMIDIAccess) return Promise.resolve(null);
  if (!_midiAccessPromise) _midiAccessPromise = navigator.requestMIDIAccess();
  return _midiAccessPromise;
}

function render({ model, el }) {
  el.innerHTML = "";

  const wrapper = document.createElement("div");
  wrapper.className = "midi-button-wrapper";

  const title = document.createElement("div");
  title.className = "midi-button-title";
  wrapper.appendChild(title);

  const btn = document.createElement("button");
  btn.className = "midi-button";
  btn.type = "button";

  const face = document.createElement("span");
  face.className = "midi-button-face";
  btn.appendChild(face);
  wrapper.appendChild(btn);

  const midiBtn = document.createElement("button");
  midiBtn.className = "midi-button-learn";
  midiBtn.type = "button";
  wrapper.appendChild(midiBtn);

  el.appendChild(wrapper);

  // --- Button behaviour ----------------------------------------------------
  // Shared by pointer events and MIDI so both paths behave identically.
  function handlePress(velocity) {
    model.set("velocity", velocity);
    model.set("press_timestamp", Date.now());
    if (model.get("mode") === "toggle") {
      model.set("value", !model.get("value"));
    } else {
      model.set("value", true);
    }
    model.save_changes();
  }

  function handleRelease() {
    // Momentary buttons drop back to false on release; toggles latch.
    if (model.get("mode") !== "toggle" && model.get("value")) {
      model.set("value", false);
      model.save_changes();
    }
  }

  function updateSize() {
    const size = model.get("size");
    btn.style.width = size + "px";
    btn.style.height = size + "px";
    // Scale the icon glyph with the pad (explicit px avoids a %-of-content loop).
    face.style.setProperty("--icon-size", Math.round(size * 0.46) + "px");
  }

  function updateFace() {
    // An icon name resolves to a bundled SVG; anything else (emoji, text) is
    // rendered literally, with the label as the fallback glyph.
    const icon = model.get("icon");
    const svg = ICONS[icon];
    if (svg) {
      face.innerHTML = svg;
      face.classList.add("has-icon");
    } else {
      face.textContent = icon || model.get("label") || "";
      face.classList.remove("has-icon");
    }
  }

  function updateTitle() {
    const text = model.get("label");
    // Show a caption above only when there's also a distinct face glyph.
    const showTitle = text && (model.get("icon") || "");
    title.textContent = showTitle ? text : "";
    title.style.display = showTitle ? "" : "none";
  }

  function updateActive() {
    btn.classList.toggle("active", model.get("value"));
  }

  function applyColor() {
    const color = model.get("color");
    if (color) {
      wrapper.style.setProperty("--midi-button-fill", color);
    } else {
      wrapper.style.removeProperty("--midi-button-fill");
    }
  }

  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    btn.setPointerCapture?.(e.pointerId);
    handlePress(127);
  });
  btn.addEventListener("pointerup", () => handleRelease());
  btn.addEventListener("pointerleave", () => handleRelease());
  btn.addEventListener("pointercancel", () => handleRelease());
  // Keyboard activation (space/enter) fires without pointer events.
  btn.addEventListener("keydown", (e) => {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      handlePress(127);
    }
  });
  btn.addEventListener("keyup", (e) => {
    if (e.key === " " || e.key === "Enter") handleRelease();
  });

  // --- MIDI (Ableton-style learn) -----------------------------------------
  let midiInputs = [];
  let midiStateBound = false;

  // Persist bindings in browser localStorage, namespaced by scope + key so two
  // notebooks (which share an origin's storage) don't collide. The default
  // scope is the browser URL path — localStorage is already per-origin, so the
  // path is all that's needed to tell sibling notebooks apart.
  function midiScope() {
    const explicit = model.get("midi_scope");
    if (explicit) return explicit;
    try {
      return window.location.pathname || "";
    } catch (e) {
      return "";
    }
  }

  function storageKey() {
    const key = model.get("midi_key") || model.get("label") || "";
    if (!key) return null;
    return `wigglystuff-midi/${midiScope()}/${key}`;
  }

  function saveBinding() {
    const sk = storageKey();
    if (!sk) return;
    try {
      localStorage.setItem(
        sk,
        JSON.stringify({
          note: model.get("midi_note"),
          channel: model.get("midi_channel"),
          device: model.get("midi_device"),
        }),
      );
    } catch (e) {
      /* storage unavailable (private mode, quota) — ignore */
    }
  }

  function clearBinding() {
    const sk = storageKey();
    if (!sk) return;
    try {
      localStorage.removeItem(sk);
    } catch (e) {
      /* ignore */
    }
  }

  function loadBinding() {
    const sk = storageKey();
    if (!sk) return null;
    try {
      const raw = localStorage.getItem(sk);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function onMidiMessage(event) {
    const [status, data1, data2] = event.data;
    const kind = status & 0xf0;
    // A note-on with velocity 0 is the conventional "note off".
    const isNoteOn = kind === 0x90 && data2 > 0;
    const isNoteOff = kind === 0x80 || (kind === 0x90 && data2 === 0);
    if (!isNoteOn && !isNoteOff) return; // notes only
    const channel = status & 0x0f;
    const note = data1;

    if (model.get("midi_learning")) {
      if (!isNoteOn) return; // learn on the press, not the release
      model.set("midi_note", note);
      model.set("midi_channel", channel);
      model.set("midi_device", event.target.name || "");
      model.set("midi_learning", false);
      model.save_changes();
      saveBinding();
      return;
    }

    const boundNote = model.get("midi_note");
    if (boundNote < 0 || note !== boundNote) return;
    const boundCh = model.get("midi_channel");
    if (boundCh >= 0 && channel !== boundCh) return;
    if (isNoteOn) handlePress(data2);
    else handleRelease();
  }

  function detachMidi() {
    for (const input of midiInputs) {
      input.removeEventListener("midimessage", onMidiMessage);
    }
    midiInputs = [];
  }

  function attachMidi(access) {
    detachMidi();
    for (const input of access.inputs.values()) {
      input.addEventListener("midimessage", onMidiMessage);
      midiInputs.push(input);
    }
  }

  async function enableMidi() {
    const access = await getMidiAccess();
    if (!access) return null;
    attachMidi(access);
    if (!midiStateBound) {
      midiStateBound = true;
      access.addEventListener("statechange", () => attachMidi(access));
    }
    return access;
  }

  function updateMidiButton() {
    if (!model.get("midi")) {
      midiBtn.style.display = "none";
      return;
    }
    midiBtn.style.display = "";
    midiBtn.classList.toggle("learning", model.get("midi_learning"));
    const note = model.get("midi_note");
    midiBtn.classList.toggle("bound", note >= 0 && !model.get("midi_learning"));
    if (!model.get("midi_supported")) {
      midiBtn.textContent = "no MIDI";
      midiBtn.disabled = true;
      midiBtn.title = "Web MIDI is not available in this browser.";
    } else if (model.get("midi_learning")) {
      midiBtn.textContent = "hit a pad…";
      midiBtn.disabled = false;
      midiBtn.title = "Press a pad/button on your MIDI device to bind it.";
    } else if (note >= 0) {
      midiBtn.textContent = `note ${note}`;
      midiBtn.disabled = false;
      midiBtn.title =
        (model.get("midi_device") || "MIDI") +
        ` · note ${note}. Click to re-learn, right-click to clear.`;
    } else {
      midiBtn.textContent = "MIDI";
      midiBtn.disabled = false;
      midiBtn.title = "Click, then hit a pad on your MIDI device.";
    }
  }

  midiBtn.addEventListener("click", async () => {
    if (!model.get("midi_supported")) return;
    if (model.get("midi_learning")) {
      model.set("midi_learning", false); // toggle off
      model.save_changes();
      return;
    }
    await enableMidi();
    model.set("midi_learning", true);
    model.save_changes();
  });

  midiBtn.addEventListener("contextmenu", (e) => {
    e.preventDefault();
    model.set("midi_note", -1);
    model.set("midi_channel", -1);
    model.set("midi_device", "");
    model.set("midi_learning", false);
    model.save_changes();
    clearBinding();
  });

  function initMidi() {
    if (!model.get("midi")) {
      updateMidiButton();
      return;
    }
    const supported = !!navigator.requestMIDIAccess;
    if (model.get("midi_supported") !== supported) {
      model.set("midi_supported", supported);
      model.save_changes();
    }
    // Restore a persisted binding when none was set explicitly in Python.
    if (model.get("midi_note") < 0) {
      const stored = loadBinding();
      if (stored && typeof stored.note === "number" && stored.note >= 0) {
        model.set("midi_note", stored.note);
        model.set(
          "midi_channel",
          typeof stored.channel === "number" ? stored.channel : -1,
        );
        model.set("midi_device", stored.device || "");
        model.save_changes();
      }
    }
    // Start listening for any active binding (explicit or restored).
    if (supported && model.get("midi_note") >= 0) enableMidi();
    updateMidiButton();
  }

  model.on("change:value", updateActive);
  model.on("change:icon", () => {
    updateFace();
    updateTitle();
  });
  model.on("change:label", () => {
    updateFace();
    updateTitle();
    updateMidiButton();
  });
  model.on("change:size", updateSize);
  model.on("change:color", applyColor);
  model.on("change:midi", initMidi);
  model.on("change:midi_learning", updateMidiButton);
  model.on("change:midi_supported", updateMidiButton);
  model.on("change:midi_note", updateMidiButton);
  model.on("change:midi_device", updateMidiButton);

  applyColor();
  updateSize();
  updateFace();
  updateTitle();
  updateActive();
  initMidi();

  return () => {
    detachMidi();
  };
}

export default { render };
