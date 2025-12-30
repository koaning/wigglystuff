function render({model, el}) {
    const config = {
        minValue: model.get("min_value"),
        maxValue: model.get("max_value"),
        stepSize: model.get("step"),
        prefix: model.get("prefix"),
        suffix: model.get("suffix"),
        digits: model.get("digits"),
        pixelsPerStep: model.get("pixels_per_step")
    };

    let amount = model.get("amount");
    console.log(amount);
    
    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";
    el.appendChild(container);

    function renderValue() {
        // Only recreate element if it doesn't exist
        let element = container.querySelector('.tangle-value');
        if (!element) {
            element = document.createElement('span');
            element.className = 'tangle-value';
            element.style.cssText = 'color: #0066cc; text-decoration: underline; cursor: ew-resize';
            element.addEventListener('mousedown', startDragging);
            container.appendChild(element);
        }
        element.textContent = config.prefix + amount.toFixed(config.digits) + config.suffix;
    }

    function updateModel() {
        model.set("amount", amount);
        model.save_changes();
    }

    let updateTimeout;
    function debouncedUpdateModel() {
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(updateModel, 16); // ~60fps throttling
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
            amount = Math.max(config.minValue, 
                           Math.min(config.maxValue, 
                                    startValue + steps * config.stepSize));
            
            // Update text content directly without full re-render
            const element = container.querySelector('.tangle-value');
            element.textContent = config.prefix + amount.toFixed(config.digits) + config.suffix;
            
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
