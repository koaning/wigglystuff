function render({model, el}) {
    const choices = model.get("choices");
    let currentIndex = choices.indexOf(model.get("choice"));
    if (currentIndex === -1) currentIndex = 0;

    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";

    el.appendChild(container);

    // Create a basic select element - keep it simple
    const select = document.createElement('select');
    select.style.color = '#0066cc';
    
    // Add options to the select element
    choices.forEach((choice, index) => {
        const option = document.createElement('option');
        option.value = choice;
        option.textContent = choice;
        option.selected = index === currentIndex;
        select.appendChild(option);
    });
    
    // Add event listener for selection change
    select.addEventListener('change', function() {
        currentIndex = this.selectedIndex;
        model.set("choice", choices[currentIndex]);
        model.save_changes();
    });
    
    container.appendChild(select);

}

export default { render };
