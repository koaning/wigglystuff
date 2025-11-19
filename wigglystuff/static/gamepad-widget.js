function render({ model, el }) {
  let currentButtonPress = model.get("current_button_press");
  let currentTimestamp = model.get("current_timestamp");
  let previousTimestamp = model.get("previous_timestamp");
  let axes = model.get("axes");
  let dpadUp = model.get("dpad_up");
  let dpadDown = model.get("dpad_down");
  let dpadLeft = model.get("dpad_left");
  let dpadRight = model.get("dpad_right");
  let isMinimized = false;

  const container = document.createElement("div");
  container.style.cssText = `
            font-family: system-ui, -apple-system, sans-serif;
            padding: 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            background: #f9fafb;
            max-width: 400px;
            transition: all 0.3s ease;
        `;

  const header = document.createElement("div");
  header.style.cssText =
    "position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 12px;";

  const title = document.createElement("h3");
  title.textContent = "🎮 Mopad Widget";
  title.style.cssText = "margin: 0; color: #374151; text-align: center;";

  const toggleButton = document.createElement("button");
  toggleButton.textContent = "−";
  toggleButton.style.cssText = `
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            background: #6b7280;
            color: white;
            border: none;
            border-radius: 4px;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
  toggleButton.onmouseover = () => (toggleButton.style.background = "#4b5563");
  toggleButton.onmouseout = () => (toggleButton.style.background = "#6b7280");

  const content = document.createElement("div");

  const status = document.createElement("div");
  status.style.cssText = `
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-weight: 500;
        `;

  const instructions = document.createElement("div");
  instructions.style.cssText =
    "font-size: 14px; color: #6b7280; margin-bottom: 12px;";

  const timestampDisplay = document.createElement("div");
  timestampDisplay.style.cssText = `
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `;

  const buttonDisplay = document.createElement("div");
  buttonDisplay.style.cssText = `
            font-size: 16px;
            color: #374151;
            padding: 4px 0;
        `;

  const dpadDisplay = document.createElement("div");
  dpadDisplay.style.cssText = `
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `;

  const axesDisplay = document.createElement("div");
  axesDisplay.style.cssText = `
            font-size: 14px;
            color: #374151;
            padding: 4px 0;
            font-family: monospace;
        `;

  header.appendChild(title);
  header.appendChild(toggleButton);
  content.appendChild(status);
  content.appendChild(instructions);
  content.appendChild(buttonDisplay);
  content.appendChild(dpadDisplay);
  content.appendChild(axesDisplay);
  content.appendChild(timestampDisplay);
  container.appendChild(header);
  container.appendChild(content);
  el.appendChild(container);

  toggleButton.addEventListener("click", () => {
    isMinimized = !isMinimized;
    if (isMinimized) {
      content.style.display = "none";
      container.style.padding = "16px";
      toggleButton.textContent = "+";
      header.style.cssText =
        "position: relative; display: flex; justify-content: center; align-items: center;";
    } else {
      content.style.display = "block";
      container.style.padding = "16px";
      toggleButton.textContent = "−";
      header.style.cssText =
        "position: relative; display: flex; justify-content: center; align-items: center; margin-bottom: 12px;";
    }
  });

  const frames =
    window.mozRequestAnimationFrame || window.requestAnimationFrame;
  let gamepadConnected = false;
  let lastGamepadState = null;

  function updateStatus(connected, gamepad = null) {
    if (connected) {
      status.style.cssText +=
        "background: #dcfce7; color: #166534; border: 1px solid #bbf7d0;";
      status.textContent = `✅ Gamepad Connected: ${gamepad?.id || "Unknown"}`;
      instructions.textContent = `Press any button on the gamepad to interact.`;
      gamepadConnected = true;
    } else {
      status.style.cssText +=
        "background: #fef2f2; color: #dc2626; border: 1px solid #fecaca;";
      status.textContent = "❌ No Gamepad Detected";
      instructions.innerHTML = `
                    To connect your gamepad:<br>
                    1. Connect your gamepad to your computer<br>
                    2. Press any button on the gamepad<br>
                    3. The widget will automatically detect it
                `;
      gamepadConnected = false;
    }
  }

  function updateButtonDisplay() {
    if (currentButtonPress >= 0) {
      buttonDisplay.textContent = `Current button press: ${currentButtonPress}`;
    } else {
      buttonDisplay.textContent = "No button pressed yet";
    }
  }

  function updateDpadDisplay() {
    const directions = [];
    if (dpadUp) directions.push("↑");
    if (dpadDown) directions.push("↓");
    if (dpadLeft) directions.push("←");
    if (dpadRight) directions.push("→");

    dpadDisplay.textContent =
      directions.length > 0
        ? `D-pad: ${directions.join(" ")}`
        : "D-pad: —";
  }

  function updateAxesDisplay() {
    if (axes && axes.length >= 4) {
      const [leftX, leftY, rightX, rightY] = axes;
      axesDisplay.innerHTML = `
                    Left stick: (${leftX.toFixed(2)}, ${leftY.toFixed(2)})<br>
                    Right stick: (${rightX.toFixed(2)}, ${rightY.toFixed(2)})
                `;
    } else {
      axesDisplay.textContent = "Sticks: No data";
    }
  }

  function updateTimestampDisplay() {
    if (currentTimestamp > 0) {
      const current = new Date(currentTimestamp).toLocaleTimeString();
      const previous =
        previousTimestamp > 0
          ? new Date(previousTimestamp).toLocaleTimeString()
          : "None";
      const timeDiff =
        previousTimestamp > 0
          ? ((currentTimestamp - previousTimestamp) / 1000).toFixed(3)
          : "N/A";
      timestampDisplay.innerHTML = `
                    Current: ${current}<br>
                    Previous: ${previous}<br>
                    Time diff: ${timeDiff}s
                `;
    } else {
      timestampDisplay.textContent = "No button presses recorded";
    }
  }

  function checkGamepadConnection() {
    const gamepads = navigator.getGamepads();
    const gamepad = gamepads[0] || gamepads[1] || gamepads[2] || gamepads[3];

    if (gamepad && gamepad.connected) {
      if (!gamepadConnected) {
        updateStatus(true, gamepad);
      }
      return gamepad;
    } else {
      if (gamepadConnected) {
        updateStatus(false);
      }
      return null;
    }
  }

  function run_loop() {
    const gamepad = checkGamepadConnection();

    if (gamepad && gamepadConnected) {
      let buttonPressed = false;
      const currentState = gamepad.buttons.map((b) => b.pressed).join("");

      if (currentState !== lastGamepadState) {
        gamepad.buttons.forEach((button, i) => {
          if (button.pressed) {
            previousTimestamp = currentTimestamp;
            currentTimestamp = Date.now();
            currentButtonPress = i;

            model.set("current_button_press", currentButtonPress);
            model.set("current_timestamp", currentTimestamp);
            model.set("previous_timestamp", previousTimestamp);
            model.save_changes();

            updateButtonDisplay();
            updateTimestampDisplay();
            buttonPressed = true;
          }
        });
      }

      if (gamepad.axes && gamepad.axes.length >= 4) {
        const newAxes = [
          Math.round((gamepad.axes[0] || 0) * 100) / 100,
          Math.round((gamepad.axes[1] || 0) * 100) / 100,
          Math.round((gamepad.axes[2] || 0) * 100) / 100,
          Math.round((gamepad.axes[3] || 0) * 100) / 100,
        ];

        const threshold = 0.05;
        let axesChanged = false;
        for (let i = 0; i < 4; i++) {
          if (Math.abs(newAxes[i] - axes[i]) > threshold) {
            axesChanged = true;
            break;
          }
        }

        if (axesChanged) {
          axes = newAxes;
          model.set("axes", axes);
          model.save_changes();
          updateAxesDisplay();
        }
      }

      const newDpadUp = gamepad.buttons[12]
        ? gamepad.buttons[12].pressed
        : false;
      const newDpadDown = gamepad.buttons[13]
        ? gamepad.buttons[13].pressed
        : false;
      const newDpadLeft = gamepad.buttons[14]
        ? gamepad.buttons[14].pressed
        : false;
      const newDpadRight = gamepad.buttons[15]
        ? gamepad.buttons[15].pressed
        : false;

      if (
        newDpadUp !== dpadUp ||
        newDpadDown !== dpadDown ||
        newDpadLeft !== dpadLeft ||
        newDpadRight !== dpadRight
      ) {
        dpadUp = newDpadUp;
        dpadDown = newDpadDown;
        dpadLeft = newDpadLeft;
        dpadRight = newDpadRight;

        model.set("dpad_up", dpadUp);
        model.set("dpad_down", dpadDown);
        model.set("dpad_left", dpadLeft);
        model.set("dpad_right", dpadRight);
        model.save_changes();
        updateDpadDisplay();
      }

      lastGamepadState = currentState;
      setTimeout(() => frames(run_loop), buttonPressed ? 200 : 50);
    } else {
      setTimeout(() => frames(run_loop), 100);
    }
  }

  window.addEventListener("gamepadconnected", (e) => {
    updateStatus(true, e.gamepad);
  });

  window.addEventListener("gamepaddisconnected", () => {
    updateStatus(false);
  });

  updateStatus(false);
  updateButtonDisplay();
  updateDpadDisplay();
  updateAxesDisplay();
  updateTimestampDisplay();

  model.on("change:current_button_press", () => {
    currentButtonPress = model.get("current_button_press");
    updateButtonDisplay();
  });

  model.on("change:current_timestamp", () => {
    currentTimestamp = model.get("current_timestamp");
    updateTimestampDisplay();
  });

  model.on("change:previous_timestamp", () => {
    previousTimestamp = model.get("previous_timestamp");
    updateTimestampDisplay();
  });

  model.on("change:axes", () => {
    axes = model.get("axes");
    updateAxesDisplay();
  });

  model.on(
    "change:dpad_up change:dpad_down change:dpad_left change:dpad_right",
    () => {
      dpadUp = model.get("dpad_up");
      dpadDown = model.get("dpad_down");
      dpadLeft = model.get("dpad_left");
      dpadRight = model.get("dpad_right");
      updateDpadDisplay();
    },
  );

  run_loop();
}

export default { render };
