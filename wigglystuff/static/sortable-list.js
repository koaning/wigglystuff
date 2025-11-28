function render({ model, el }) {
  el.classList.add("draggable-list-widget");

  let draggedItem = null;
  let draggedIndex = null;
  let dropTarget = null;
  let dropPosition = null;

  function renderList() {
    el.replaceChildren();

    // Render label if provided
    let labelText = model.get("label");
    if (labelText) {
      let labelElement = document.createElement("label");
      labelElement.className = "list-label";
      labelElement.textContent = labelText;
      el.appendChild(labelElement);
    }

    let container = document.createElement("div");
    container.className = "list-container";

    model.get("value").forEach((item, index) => {
      let listItem = document.createElement("div");
      listItem.className = "list-item";
      listItem.draggable = true;
      listItem.dataset.index = index;

      let dragHandle = document.createElement("button");
      dragHandle.className = "drag-handle";
      dragHandle.innerHTML = `
        <svg width="10" height="10" viewBox="0 0 16 16">
          <circle cx="4" cy="4" r="1"/>
          <circle cx="12" cy="4" r="1"/>
          <circle cx="4" cy="8" r="1"/>
          <circle cx="12" cy="8" r="1"/>
          <circle cx="4" cy="12" r="1"/>
          <circle cx="12" cy="12" r="1"/>
        </svg>
      `;
      dragHandle.setAttribute("aria-label", `Reorder ${item}`);

      let label = document.createElement("span");
      label.className = "item-label";
      label.textContent = item;
      
      if (model.get("editable")) {
        label.classList.add("editable");
        label.setAttribute("tabindex", "0");
        label.onclick = (e) => {
          e.stopPropagation();
          startEdit(label, index);
        };
        label.onkeydown = (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            e.stopPropagation();
            startEdit(label, index);
          }
        };
      }

      let removeButton = null;
      if (model.get("removable")) {
        removeButton = document.createElement("button");
        removeButton.className = "remove-button";
        removeButton.innerHTML = `
          <svg width="10" height="10" viewBox="0 0 14 14" fill="none">
            <path d="M4 4l6 6m0-6l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        `;
        removeButton.setAttribute("aria-label", `Remove ${item}`);
        removeButton.onclick = (e) => {
          e.stopPropagation();
          removeItem(index);
        };
      }

      listItem.appendChild(dragHandle);
      listItem.appendChild(label);
      if (removeButton) {
        listItem.appendChild(removeButton);
      }

      listItem.addEventListener("dragstart", (e) => {
        draggedItem = listItem;
        draggedIndex = index;
        listItem.classList.add("dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/html", listItem.outerHTML);
      });

      listItem.addEventListener("dragend", () => {
        listItem.classList.remove("dragging");
        draggedItem = null;
        draggedIndex = null;
        clearDropIndicators();
      });

      listItem.addEventListener("dragover", (e) => {
        if (draggedItem && draggedItem !== listItem) {
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";

          let rect = listItem.getBoundingClientRect();
          let midpoint = rect.top + rect.height / 2;
          let newDropPosition = e.clientY < midpoint ? "top" : "bottom";

          if (dropTarget !== listItem || dropPosition !== newDropPosition) {
            clearDropIndicators();
            dropTarget = listItem;
            dropPosition = newDropPosition;
            showDropIndicator(listItem, newDropPosition);
          }
        }
      });

      listItem.addEventListener("dragleave", (e) => {
        if (!listItem.contains(e.relatedTarget)) {
          clearDropIndicators();
        }
      });

      listItem.addEventListener("drop", (e) => {
        e.preventDefault();
        if (draggedItem && draggedItem !== listItem) {
          let targetIndex = parseInt(listItem.dataset.index);
          let newIndex = targetIndex;

          if (dropPosition === "bottom") {
            newIndex = targetIndex + 1;
          }

          if (draggedIndex < newIndex) {
            newIndex--;
          }

          reorderItems(draggedIndex, newIndex);
        }
        clearDropIndicators();
      });

      container.appendChild(listItem);
    });

    el.appendChild(container);

    if (model.get("addable")) {
      let addInput = document.createElement("input");
      addInput.type = "text";
      addInput.className = "add-input";
      addInput.placeholder = "Add new item...";
      addInput.onkeydown = (e) => {
        if (e.key === "Enter" && addInput.value.trim()) {
          e.preventDefault();
          addItem(addInput.value.trim());
          addInput.value = "";
          addInput.focus();
        }
      };

      el.appendChild(addInput);
    }
  }

  function addItem(text) {
    model.set("value", [...model.get("value"), text]);
    model.save_changes();
  }

  function removeItem(index) {
    model.set("value",  model.get("value").toSpliced(index, 1));
    model.save_changes();
  }

  function showDropIndicator(element, position) {
    let indicator = document.createElement("div");
    indicator.className = "drop-indicator";
    indicator.style.position = "absolute";
    indicator.style.left = "0";
    indicator.style.right = "0";
    indicator.style.height = "2px";
    indicator.style.backgroundColor = "#0066cc";
    indicator.style.zIndex = "1000";

    if (position === "top") {
      indicator.style.top = "-1px";
    } else {
      indicator.style.bottom = "-1px";
    }

    element.style.position = "relative";
    element.appendChild(indicator);
  }

  function clearDropIndicators() {
    el.querySelectorAll(".drop-indicator").forEach(indicator => {
      indicator.remove();
    });
    dropTarget = null;
    dropPosition = null;
  }

  function reorderItems(fromIndex, toIndex) {
    let items = [...model.get("value")];
    let [movedItem] = items.splice(fromIndex, 1);
    items.splice(toIndex, 0, movedItem);
    model.set("value", items);
    model.save_changes();
  }

  function startEdit(label, index) {
    let currentText = label.textContent;
    let input = document.createElement("input");
    input.type = "text";
    input.className = "edit-input";
    input.value = currentText;
    
    function finishEdit(save = false) {
      if (save && input.value.trim() && input.value.trim() !== currentText) {
        let items = [...model.get("value")];
        items[index] = input.value.trim();
        model.set("value", items);
        model.save_changes();
      } else {
        label.textContent = currentText;
        label.style.display = "";
        input.remove();
      }
    }
    
    input.onblur = () => finishEdit(true);
    input.onkeydown = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        finishEdit(true);
      } else if (e.key === "Escape") {
        e.preventDefault();
        finishEdit(false);
      }
      e.stopPropagation();
    };
    
    label.style.display = "none";
    label.parentNode.insertBefore(input, label.nextSibling);
    input.focus();
    input.select();
  }

  renderList();
  model.on("change:value", renderList);
  model.on("change:label", renderList);
}

export default { render };