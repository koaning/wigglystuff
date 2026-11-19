function render({model, el}) {
    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";

    el.appendChild(container);

    // Create a basic select element - keep it simple
    const select = document.createElement('select');
    select.style.color = '#0066cc';

    // (Re)build the options from the model, so Python can swap the choices
    // on a live widget.
    function renderOptions() {
        const choices = model.get("choices");
        select.replaceChildren();
        choices.forEach((choice) => {
            const option = document.createElement('option');
            option.value = choice;
            option.textContent = choice;
            select.appendChild(option);
        });
        const index = choices.indexOf(model.get("choice"));
        select.selectedIndex = index === -1 ? 0 : index;
    }
    renderOptions();

    // Add event listener for selection change
    select.addEventListener('change', function() {
        model.set("choice", model.get("choices")[this.selectedIndex]);
        model.save_changes();
    });

    // Listen for external changes to choice and choices
    model.on("change:choice", renderOptions);
    model.on("change:choices", renderOptions);

    container.appendChild(select);

}

export default { render };
