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
    let steps = model.get("steps");
    let editing = false;

    const container = document.createElement('div');
    container.classList.add("tangle-container");
    el.style.display = "inline-flex";
    el.appendChild(container);

    // Listen for external changes to all config traitlets
    ["amount", "min_value", "max_value", "step", "steps", "prefix", "suffix", "digits", "pixels_per_step"].forEach(name => {
        model.on(`change:${name}`, () => {
            config.minValue = model.get("min_value");
            config.maxValue = model.get("max_value");
            config.stepSize = model.get("step");
            config.prefix = model.get("prefix");
            config.suffix = model.get("suffix");
            config.digits = model.get("digits");
            config.pixelsPerStep = model.get("pixels_per_step");
            amount = model.get("amount");
            steps = model.get("steps");
            // Ignore external syncs while the user is typing a value.
            if (!editing) renderValue();
        });
    });

    function renderValue() {
        container.innerHTML = '';
        const element = document.createElement('span');
        element.className = 'tangle-value';
        element.style.color = '#0066cc';
        element.style.textDecoration = 'underline';
        element.style.cursor = 'ew-resize';
        element.textContent = config.prefix + amount.toFixed(config.digits) + config.suffix;
        element.addEventListener('mousedown', startDragging);
        container.appendChild(element);
    }

    function updateModel() {
        model.set("amount", amount);
        model.save_changes();
    }

    let updateTimeout;
    function debouncedUpdateModel() {
        clearTimeout(updateTimeout);
        updateTimeout = setTimeout(updateModel, 50); // Debounce for 100ms
    }

    function startDragging(e) {
        e.preventDefault();
        const element = e.target;
        element.style.cursor = 'grabbing';
        const startX = e.clientX;
        const startValue = parseFloat(element.textContent.replace(config.prefix, '').replace(config.suffix, ''));
        const startIndex = steps.length > 0 ? Math.max(0, steps.indexOf(amount)) : -1;
        let moved = false;

        function onMouseMove(e) {
            const deltaX = e.clientX - startX;
            if (Math.abs(deltaX) > 3) moved = true;
            const pixelSteps = Math.floor(deltaX / config.pixelsPerStep);
            if (steps.length > 0) {
                const newIndex = Math.max(0, Math.min(steps.length - 1, startIndex + pixelSteps));
                amount = steps[newIndex];
            } else {
                amount = Math.max(config.minValue,
                               Math.min(config.maxValue,
                                        startValue + pixelSteps * config.stepSize));
            }
            renderValue();
            debouncedUpdateModel();
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            element.style.cursor = 'ew-resize';
            // A click without a real drag enters edit mode (linear sliders only).
            if (!moved && steps.length === 0) {
                amount = startValue;
                enterEditMode();
            } else {
                updateModel();
            }
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    function enterEditMode() {
        editing = true;
        const previous = amount;
        let finished = false;

        container.innerHTML = '';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'tangle-input';
        input.value = amount.toFixed(config.digits);
        // Match the value's look and keep it inline so the layout doesn't jump.
        input.style.color = '#0066cc';
        input.style.font = 'inherit';
        input.style.background = 'transparent';
        input.style.border = 'none';
        input.style.borderBottom = '1px solid #0066cc';
        input.style.padding = '0';
        input.style.margin = '0';
        input.style.width = `${Math.max(input.value.length + 1, 2)}ch`;
        container.appendChild(input);
        input.focus();
        input.select();

        function finish(commit) {
            if (finished) return;
            finished = true;
            editing = false;
            if (commit) {
                const parsed = parseFloat(input.value);
                if (!isNaN(parsed)) {
                    let next = Math.max(config.minValue, Math.min(config.maxValue, parsed));
                    // Snap to the step grid anchored at min_value, then re-clamp.
                    if (config.stepSize > 0) {
                        next = config.minValue + Math.round((next - config.minValue) / config.stepSize) * config.stepSize;
                        next = Math.max(config.minValue, Math.min(config.maxValue, next));
                    }
                    amount = next;
                } else {
                    amount = previous; // Non-numeric input: restore previous value.
                }
            } else {
                amount = previous; // Escape / blur cancels.
            }
            renderValue();
            updateModel();
        }

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                finish(true);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                finish(false);
            }
        });
        input.addEventListener('blur', () => finish(false));
    }

    renderValue();
}

export default { render };
