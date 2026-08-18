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
    // Literal text the user last typed (e.g. "2.5e-3"). When set, the value is
    // shown verbatim so scientific notation stays legible; cleared on any drag
    // or Python-side change so those revert to toFixed(digits) formatting.
    let lastTypedText = null;

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
            // A Python-side change supersedes any typed literal.
            lastTypedText = null;
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
        const shown = lastTypedText !== null ? lastTypedText : amount.toFixed(config.digits);
        element.textContent = config.prefix + shown + config.suffix;
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

    // Modifier scaling for linear sliders: Shift = 10x coarser, Alt/Option =
    // 10x finer (Alt wins if both are held). Discrete steps mode ignores this.
    function modMultiplier(ev) {
        if (ev.altKey) return 0.1;
        if (ev.shiftKey) return 10;
        return 1;
    }

    function startDragging(e) {
        e.preventDefault();
        const element = e.target;
        element.style.cursor = 'grabbing';
        // Anchor (startX/startValue) is mutable so we can rebase it when the
        // modifier changes mid-drag, keeping the value from jumping.
        let startX = e.clientX;
        let startValue = amount;
        let lastX = startX;
        let curMult = 1;
        const startIndex = steps.length > 0 ? Math.max(0, steps.indexOf(amount)) : -1;
        let moved = false;

        function applyMove(clientX, mult) {
            if (mult !== curMult) {
                // Rebase the anchor so future movement rescales from here.
                startX = clientX;
                startValue = amount;
                curMult = mult;
            }
            const deltaX = clientX - startX;
            if (Math.abs(deltaX) > 3) moved = true;
            const pixelSteps = Math.floor(deltaX / config.pixelsPerStep);
            if (steps.length > 0) {
                const newIndex = Math.max(0, Math.min(steps.length - 1, startIndex + pixelSteps));
                amount = steps[newIndex];
            } else {
                amount = Math.max(config.minValue,
                               Math.min(config.maxValue,
                                        startValue + pixelSteps * config.stepSize * mult));
            }
            renderValue();
            debouncedUpdateModel();
        }

        function onMouseMove(e) {
            lastTypedText = null; // dragging supersedes any typed literal
            lastX = e.clientX;
            const mult = steps.length > 0 ? 1 : modMultiplier(e);
            applyMove(e.clientX, mult);
        }

        function onKeyChange(e) {
            if (steps.length > 0) return; // linear mode only
            applyMove(lastX, modMultiplier(e));
        }

        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            document.removeEventListener('keydown', onKeyChange);
            document.removeEventListener('keyup', onKeyChange);
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
        document.addEventListener('keydown', onKeyChange);
        document.addEventListener('keyup', onKeyChange);
    }

    function enterEditMode() {
        editing = true;
        const previous = amount;
        const previousTypedText = lastTypedText;
        let finished = false;

        container.innerHTML = '';
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'tangle-input';
        input.value = lastTypedText !== null ? lastTypedText : amount.toFixed(config.digits);
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
                    // Clamp to bounds but do NOT snap to the step grid, so exact
                    // values (incl. scientific notation like 2.5e-3) survive.
                    const next = Math.max(config.minValue, Math.min(config.maxValue, parsed));
                    amount = next;
                    // Show the literal text only when accepted unchanged; a
                    // clamped value renders as the clamped number via toFixed.
                    lastTypedText = next === parsed ? input.value.trim() : null;
                } else {
                    amount = previous; // Non-numeric input: restore previous value.
                    lastTypedText = previousTypedText;
                }
            } else {
                amount = previous; // Escape / blur cancels.
                lastTypedText = previousTypedText;
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
