function render({model, el}) {
    const choices = model.get("choices");
    let currentIndex = choices.indexOf(model.get("choice"));
    if (currentIndex === -1) currentIndex = 0;

    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";

    el.appendChild(container);

    function renderValue() {
        container.innerHTML = '';
        const element = document.createElement('span');
        element.className = 'tangle-value';
        element.style.color = '#0066cc';
        element.style.textDecoration = 'underline';
        element.style.cursor = 'pointer';
        element.textContent = choices[currentIndex];
        element.addEventListener('click', cycleChoice);
        container.appendChild(element);
    }

    function cycleChoice() {
        currentIndex = (currentIndex + 1) % choices.length;
        renderValue();
        updateModel();
    }

    function updateModel() {
        model.set("choice", choices[currentIndex]);
        model.save_changes();
    }

    // Listen for external changes to choice
    model.on("change:choice", () => {
        const newChoice = model.get("choice");
        const newIndex = choices.indexOf(newChoice);
        if (newIndex !== -1) {
            currentIndex = newIndex;
            renderValue();
        }
    });

    renderValue();
    updateModel();
}

export default { render };
