function render({ model, el }) {
  el.classList.add("env-config-widget");

  const container = document.createElement("div");
  container.className = "env-config-container";

  // Store references to update in place (no DOM rebuild)
  const rows = [];
  const inputs = [];
  const statusEls = [];
  let footer;

  function buildInitialDOM() {
    const variables = model.get("variables");

    variables.forEach((variable, index) => {
      const row = document.createElement("div");
      row.className = "env-config-row";
      row.dataset.status = variable.status;
      rows.push(row);

      // Variable name
      const nameEl = document.createElement("div");
      nameEl.className = "env-var-name";
      nameEl.textContent = variable.name;
      row.appendChild(nameEl);

      // Input field
      const fieldEl = document.createElement("div");
      fieldEl.className = "env-var-field";

      const input = document.createElement("input");
      input.type = "password";
      input.className = "env-input";
      input.autocomplete = "off";
      inputs.push(input);

      // Set initial value/placeholder - show value even for invalid status
      if (variable.status === "valid" || variable.status === "invalid") {
        input.value = variable.value || "";
      }
      if (variable.status === "missing") {
        input.placeholder = "Enter value...";
      }

      // Submit on Enter only - let Tab work naturally
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          const value = input.value.trim();
          if (!value) return;

          model.set("_pending_value", {
            name: variable.name,
            value: value,
          });
          model.save_changes();
        }
      });

      fieldEl.appendChild(input);
      row.appendChild(fieldEl);

      // Status indicator
      const statusEl = document.createElement("div");
      statusEl.className = "env-var-status";
      statusEls.push(statusEl);
      updateStatusIcon(statusEl, variable);

      row.appendChild(statusEl);
      container.appendChild(row);
    });

    // Footer
    footer = document.createElement("div");
    updateFooter();
    container.appendChild(footer);

    el.appendChild(container);
  }

  function updateStatusIcon(statusEl, variable) {
    if (variable.status === "valid") {
      statusEl.innerHTML = `
        <svg class="env-check" viewBox="0 0 24 24" width="18" height="18">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor"/>
        </svg>
      `;
    } else if (variable.status === "invalid") {
      statusEl.innerHTML = `
        <span class="env-error-text" title="${variable.error || "Invalid"}">
          <svg class="env-error-icon" viewBox="0 0 24 24" width="18" height="18">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="currentColor"/>
          </svg>
        </span>
      `;
    } else {
      statusEl.innerHTML = "";
    }
  }

  function updateFooter() {
    const allValid = model.get("all_valid");
    footer.className = "env-config-footer";
    footer.textContent = allValid
      ? "All variables configured"
      : "Press Enter to set each variable";
  }

  function updateInPlace() {
    const variables = model.get("variables");

    variables.forEach((variable, index) => {
      const row = rows[index];
      const input = inputs[index];
      const statusEl = statusEls[index];

      // Update row status (for background color)
      row.dataset.status = variable.status;

      // Update input based on status - show value even for invalid status
      if (variable.status === "valid" || variable.status === "invalid") {
        // Only update value if it changed (avoid overwriting while user types)
        if (input.value !== variable.value) {
          input.value = variable.value || "";
        }
        input.placeholder = "";
      } else {
        input.placeholder = "Enter value...";
      }

      // Update status icon
      updateStatusIcon(statusEl, variable);
    });

    updateFooter();
  }

  buildInitialDOM();
  model.on("change:variables", updateInPlace);
}

export default { render };
