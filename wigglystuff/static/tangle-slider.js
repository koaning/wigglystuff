function render({model, el}) {
    const config = {
        minValue: model.get("min_value"),
        maxValue: model.get("max_value"),
        stepSize: model.get("step"),
        prefix: model.get("prefix"),
        suffix: model.get("suffix"),
        digits: model.get("digits"),
        pixelsPerStep: 2
    };

    let value = model.get("value");
    
    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.appendChild(container);

    function renderValue() {
        console.log(config.prefix + value.toFixed(1) + config.suffix);
        container.innerHTML = '';
        const element = document.createElement('span');
        element.className = 'tangle-value';
        element.style.color = '#0066cc';
        element.style.textDecoration = 'underline';
        element.style.cursor = 'ew-resize';
        element.textContent = config.prefix + value.toFixed(config.digits) + config.suffix;
        element.addEventListener('mousedown', startDragging);
        container.appendChild(element);
    }

    function updateModel() {
        model.set("value", value);
        model.save_changes();
    }

    let updateTimeout;
    function debouncedUpdateModel() {
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(updateModel, 100); // Debounce for 100ms
    }

    function startDragging(e) {
        e.preventDefault();
        const element = e.target;
        element.style.cursor = 'grabbing';
        const startX = e.clientX;
        const startValue = parseFloat(element.textContent.replace(config.prefix, '').replace(config.suffix, ''));

        function onMouseMove(e) {
            const deltaX = e.clientX - startX;
            const steps = Math.floor(deltaX / config.pixelsPerStep);
            value = Math.max(config.minValue, 
                           Math.min(config.maxValue, 
                                  startValue + steps * config.stepSize));
            renderValue();
            debouncedUpdateModel();
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            element.style.cursor = 'ew-resize';
            updateModel();
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    renderValue();
}

export default { render };
